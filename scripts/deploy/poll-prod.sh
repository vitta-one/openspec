#!/usr/bin/env bash
# Deploy por pull, sem secrets no GitHub. Executado na VPS pelo systemd timer.
set -Eeuo pipefail
umask 077

REPO='vitta-one/openspec'
BRANCH='prod'
APP_USER='vitta-one'
SOURCE='/srv/vitta-one'
RELEASES='/srv/vitta-one-releases'
CURRENT='/srv/vitta-one-current'
STATE_DIR='/var/lib/vitta-one-deploy'
ENV_FILE='/etc/vitta-one/vitta-one.env'
DOMAIN='vitta.salles.dev.br'
SERVICE='vitta-one.service'

[[ "$(id -u)" -eq 0 ]] || { echo 'Executar como root (systemd).'; exit 1; }
for path in "$SOURCE/.git" "$ENV_FILE" "$CURRENT" "$RELEASES"; do
  [[ -e "$path" ]] || { echo "Pré-requisito ausente: $path"; exit 1; }
done

exec 9>/run/lock/vitta-one-prod-deploy.lock
flock -n 9 || { echo 'Outra implantação em andamento.'; exit 0; }

as_app() { runuser -u "$APP_USER" -- "$@"; }

# Buscar SHA do branch remoto sem modificar a árvore live.
as_app git -C "$SOURCE" fetch --no-tags origin \
  "refs/heads/$BRANCH:refs/remotes/origin/$BRANCH"
SHA="$(as_app git -C "$SOURCE" rev-parse "refs/remotes/origin/$BRANCH")"
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || exit 1

INSTALLED="$(cat "$STATE_DIR/current.sha" 2>/dev/null || true)"
if [[ "$SHA" == "$INSTALLED" ]]; then
  echo "Versão $SHA já está publicada."
  exit 0
fi
if [[ "$SHA" == "$(cat "$STATE_DIR/failed.sha" 2>/dev/null || true)" ]]; then
  echo "Versão $SHA bloqueada após falha anterior. Aguarde novo commit em prod."
  exit 0
fi

# O SHA deve ter passado no workflow CI Produção (evento push, não PR/manual).
RUNS_URL="https://api.github.com/repos/$REPO/actions/workflows/production-ci.yml/runs?branch=$BRANCH&event=push&head_sha=$SHA&per_page=10"
RUNS_JSON="$(curl --fail --silent --show-error --connect-timeout 8 --max-time 20 \
  -H 'Accept: application/vnd.github+json' \
  -H 'User-Agent: vitta-one-cd' "$RUNS_URL")"
if ! printf '%s' "$RUNS_JSON" | python3 -c '
import json, sys
obj=json.load(sys.stdin)
sha=sys.argv[1]
runs=obj.get("workflow_runs", [])
ok=any(r.get("head_sha")==sha and r.get("event")=="push"
       and r.get("status")=="completed" and r.get("conclusion")=="success"
       and r.get("head_branch")=="prod" for r in runs)
raise SystemExit(0 if ok else 1)
' "$SHA"; then
  echo "CI do SHA $SHA ainda não passou. Deploy bloqueado."
  exit 0
fi

# Credenciais de produção só entram no ambiente após instalar dependências.
load_runtime_env() {
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
  [[ -n "${DATABASE_URL:-}" ]] || { echo 'DATABASE_URL ausente'; exit 1; }
  [[ "${VITTA_ONE_LOCAL_ADMIN_PREVIEW:-false}" != "true" ]] || {
    echo 'Preview de administrador QA não pode estar ativo em produção.'; exit 1;
  }
}

WORK=''
SWITCHED=0
PREVIOUS="$(readlink -f "$CURRENT")"
cleanup() {
  rc=$?
  trap - EXIT
  if [[ "$SWITCHED" == 1 && "$rc" -ne 0 ]]; then
    echo 'Falha no deploy, restaurando versão anterior.'
    ln -s "$PREVIOUS" "$CURRENT.rollback"
    mv -Tf "$CURRENT.rollback" "$CURRENT"
    systemctl restart "$SERVICE" || true
    printf '%s\n' "$SHA" > "$STATE_DIR/failed.sha"
  fi
  if [[ -n "$WORK" && -d "$WORK" ]]; then
    rm -rf -- "$WORK"
  fi
  exit "$rc"
}
trap cleanup EXIT

mkdir -p "$STATE_DIR"
chmod 700 "$STATE_DIR"

RELEASE="$RELEASES/$SHA"
if [[ ! -f "$RELEASE/.ready" ]]; then
  WORK="$(as_app mktemp -d "$RELEASES/.building-${SHA:0:12}.XXXXXXXX")"
  echo "Preparando release $SHA..."
  as_app git -C "$SOURCE" archive "$SHA" | as_app tar -xf - -C "$WORK"
  as_app python3.12 -m venv "$WORK/.venv"
  as_app "$WORK/.venv/bin/python" -m pip install --disable-pip-version-check \
    -r "$WORK/requirements.txt"
  pushd "$WORK" >/dev/null
  load_runtime_env
  as_app "$WORK/.venv/bin/alembic" current --check-heads
  as_app "$WORK/.venv/bin/reflex" compile --dry
  popd >/dev/null
  as_app touch "$WORK/.ready"
  mv -T "$WORK" "$RELEASE"
  WORK=''
fi

# Migração pode ter ocorrido entre a validação e o swap: confira de novo.
load_runtime_env
pushd "$RELEASE" >/dev/null
as_app "$RELEASE/.venv/bin/alembic" current --check-heads
popd >/dev/null

# Swap atômico de symlink; o serviço ainda segue vivo até o restart.
ln -s "$RELEASE" "$CURRENT.next"
mv -Tf "$CURRENT.next" "$CURRENT"
SWITCHED=1

if ! systemctl restart "$SERVICE"; then
  echo 'systemctl restart falhou'
  exit 1
fi

READY=0
for _ in $(seq 1 90); do
  if systemctl is-active --quiet "$SERVICE" && \
    curl --fail --silent --show-error --location --max-time 4 \
      'http://172.16.1.1:18080/login' -o /dev/null 2>/dev/null && \
    curl --fail --silent --show-error --location --max-time 4 \
      --resolve "$DOMAIN:443:127.0.0.1" \
      "https://$DOMAIN/login" -o /dev/null 2>/dev/null; then
    READY=1
    break
  fi
  sleep 2
done
[[ "$READY" == 1 ]] || { echo 'Health check falhou'; exit 1; }

printf '%s\n' "$SHA" > "$STATE_DIR/current.sha"
SWITCHED=0
# Atualize o próprio agente somente depois do deploy ter sido validado.
install -o root -g root -m 750 "$RELEASE/scripts/deploy/poll-prod.sh" \
  /usr/local/libexec/vitta-one-deploy/poll-prod.sh
logger -t vitta-one-cd "Deploy aprovado: $SHA"
echo "Deploy publicado e validado: $SHA"
