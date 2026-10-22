#!/usr/bin/env bash
# Ambiente de desenvolvimento local: PostgreSQL via Docker + Reflex no host.
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-dev}"
case "$MODE" in
  dev|admin|db-only) ;;
  *) echo "Uso: bash scripts/dev-local.sh [dev|admin|db-only]" >&2; exit 2 ;;
esac

require() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Ferramenta ausente: $1. Instale-a antes de iniciar." >&2
    exit 1
  fi
}

require docker
require python3.12
docker compose version >/dev/null 2>&1 || {
  echo "Instale o Docker Compose V2 (comando: docker compose)." >&2
  exit 1
}
docker info >/dev/null 2>&1 || {
  echo "O Docker não está acessível. Inicie o Docker Desktop/serviço Docker e confira as permissões." >&2
  exit 1
}

ENV_FILE="$ROOT_DIR/.env.docker"
if [[ -L "$ENV_FILE" ]]; then
  echo "Recusado: .env.docker não pode ser um link simbólico." >&2
  exit 1
fi
if [[ ! -f "$ENV_FILE" ]]; then
  if docker volume inspect vitta_one_dev_pgdata >/dev/null 2>&1; then
    echo "O volume PostgreSQL já existe, mas .env.docker está ausente." >&2
    echo "Recupere as credenciais originais; o banco existente NÃO será apagado." >&2
    exit 1
  fi
  umask 077
  DB_PASSWORD="$(python3.12 -c 'import secrets; print(secrets.token_hex(24))')"
  cat > "$ENV_FILE" <<EOF
# Gerado localmente; não versionar ou compartilhar.
POSTGRES_USER=vittaqa
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=vitta_one_qa
DATABASE_URL=postgresql+psycopg://vittaqa:${DB_PASSWORD}@127.0.0.1:5433/vitta_one_qa
VITTA_ONE_SESSION_TTL_SECONDS=3600
VITTA_ONE_COOKIE_SECURE=false
VITTA_ONE_CLINIC_TIMEZONE=America/Sao_Paulo
VITTA_ONE_LOCAL_ADMIN_PREVIEW=true
REFLEX_TELEMETRY_ENABLED=false
EOF
  echo "Arquivo de configuração local criado (somente leitura para seu usuário)."
fi
chmod 600 "$ENV_FILE"

set -a
# Este arquivo é gerado pelo próprio script e só deve conter as variáveis locais.
source "$ENV_FILE"
set +a

# Falhar fechado: migrations jamais podem atingir um banco que não seja o QA
# isolado no Docker. NÃO ativar o flag de seed destrutivo usado pelo CI.
python3.12 - <<'PY'
import os
from urllib.parse import urlsplit

db = urlsplit(os.environ.get("DATABASE_URL", ""))
assert (db.scheme, db.hostname, db.port, db.path, db.username) == (
    "postgresql+psycopg", "127.0.0.1", 5433, "/vitta_one_qa", "vittaqa"
), "DATABASE_URL deve apontar exclusivamente para o QA local 127.0.0.1:5433/vitta_one_qa"
assert db.password == os.environ.get("POSTGRES_PASSWORD"), "Senhas do banco divergentes"
assert os.environ.get("POSTGRES_USER") == "vittaqa", "Usuário do Docker divergente"
assert os.environ.get("POSTGRES_DB") == "vitta_one_qa", "Banco do Docker divergente"
assert os.environ.get("VITTA_ONE_QA_DISPOSABLE_DATABASE") != "yes", (
    "Não execute o seed destrutivo de CI no banco persistente."
)
print("Banco verificado: 127.0.0.1:5433 / vitta_one_qa (Docker isolado).")
PY

COMPOSE=(docker compose -p vitta-one-local --env-file "$ENV_FILE" -f "$ROOT_DIR/compose.dev.yaml")
echo "Iniciando PostgreSQL 16..."
"${COMPOSE[@]}" up -d --wait db

if [[ "$MODE" == "db-only" ]]; then
  echo "PostgreSQL disponível em 127.0.0.1:5433; dados persistidos no volume Docker."
  exit 0
fi

if [[ ! -x "$ROOT_DIR/.venv/bin/python" ]]; then
  echo "Criando ambiente Python 3.12..."
  python3.12 -m venv "$ROOT_DIR/.venv"
fi
VENV_PY="$ROOT_DIR/.venv/bin/python"
VENV_REFLEX="$ROOT_DIR/.venv/bin/reflex"
if [[ "$("$VENV_PY" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" != "3.12" ]]; then
  echo "A .venv atual não é Python 3.12. Preserve-a e renomeie antes de recriar." >&2
  exit 1
fi

DEPS_HASH="$(python3.12 - <<'PY'
import hashlib
from pathlib import Path

files = [Path("requirements.txt"), Path("requirements-dev.txt")]
digest = hashlib.sha256()
for file in files:
    digest.update(file.name.encode())
    digest.update(file.read_bytes())
print(digest.hexdigest())
PY
)"
STAMP="$ROOT_DIR/.venv/.vitta-one-dev-requirements"
if [[ ! -f "$STAMP" ]] || [[ "$(cat "$STAMP")" != "$DEPS_HASH" ]] || \
  ! "$VENV_PY" -m pip show reflex psycopg pytest >/dev/null 2>&1; then
  echo "Instalando dependências Python (somente no primeiro uso ou quando mudarem)..."
  "$VENV_PY" -m pip install -r requirements-dev.txt
  printf '%s\n' "$DEPS_HASH" > "$STAMP"
fi

echo "Aplicando migrations no PostgreSQL LOCAL..."
"$VENV_REFLEX" db migrate

if [[ "$MODE" == "admin" ]]; then
  if [[ ! -t 0 ]]; then
    echo "Abra um terminal interativo para cadastrar o Administrador." >&2
    exit 1
  fi
  read -r -p "E-mail do Administrador local: " VITTA_ONE_BOOTSTRAP_ADMIN_EMAIL
  read -r -s -p "Senha forte (sem exibir no terminal): " VITTA_ONE_BOOTSTRAP_ADMIN_PASSWORD
  printf '\n'
  export VITTA_ONE_BOOTSTRAP_ADMIN_EMAIL VITTA_ONE_BOOTSTRAP_ADMIN_PASSWORD
  "$VENV_PY" -m vitta_one.auth.bootstrap
  unset VITTA_ONE_BOOTSTRAP_ADMIN_EMAIL VITTA_ONE_BOOTSTRAP_ADMIN_PASSWORD
  echo "Acesse http://localhost:3000/login após 'make dev'."
  exit 0
fi

echo "PostgreSQL pronto e migrations aplicadas."
echo "Abrindo Vitta-One em http://localhost:3000/login (Ctrl+C encerra o Reflex; o banco persiste)."
exec "$VENV_REFLEX" run --env dev
