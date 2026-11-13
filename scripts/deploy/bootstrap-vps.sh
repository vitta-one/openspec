#!/usr/bin/env bash
# Instala atualização automática sem chaves SSH ou GitHub secrets.
set -Eeuo pipefail
[[ "$(id -u)" == 0 ]] || { echo 'Execute como root.'; exit 1; }

SOURCE='/srv/vitta-one'
CURRENT='/srv/vitta-one-current'
RELEASES='/srv/vitta-one-releases'
STATE='/var/lib/vitta-one-deploy'
BIN='/usr/local/libexec/vitta-one-deploy'

[[ -d "$SOURCE/.git" ]] || { echo "Repositório ausente em $SOURCE"; exit 1; }
[[ -f /etc/vitta-one/vitta-one.env ]] || { echo 'Ambiente existente da VPS não encontrado'; exit 1; }
systemctl is-active --quiet vitta-one.service || { echo 'Reflex atual não está ativo'; exit 1; }

install -d -m 750 -o vitta-one -g vitta-one "$RELEASES"
install -d -m 700 "$STATE"
install -d -m 750 "$BIN"
install -d -m 755 /etc/systemd/system/vitta-one.service.d

if [[ ! -e "$CURRENT" ]]; then
  ln -s "$SOURCE" "$CURRENT"
fi
[[ -L "$CURRENT" && -d "$CURRENT/.venv" ]] || { echo 'Current deve ser symlink para release com venv'; exit 1; }

# Preserva as variáveis de /etc/vitta-one/vitta-one.env e a porta já configurada.
# O próximo restart passará a usar a release selecionada pelo symlink.
cat > /etc/systemd/system/vitta-one.service.d/20-cd-current.conf <<'UNIT'
[Service]
WorkingDirectory=/srv/vitta-one-current
ExecStart=
ExecStart=/srv/vitta-one-current/.venv/bin/reflex run --env prod --frontend-port 18080 --backend-host 172.16.1.1
UNIT

install -o root -g root -m 750 \
  "$(cd "$(dirname "$0")" && pwd)/poll-prod.sh" \
  "$BIN/poll-prod.sh"

cat > /etc/systemd/system/vitta-one-prod-deploy.service <<'UNIT'
[Unit]
Description=Atualizar Vitta One apos CI verde na branch prod
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/libexec/vitta-one-deploy/poll-prod.sh
TimeoutStartSec=900
Nice=10
UNIT

cat > /etc/systemd/system/vitta-one-prod-deploy.timer <<'UNIT'
[Unit]
Description=Verificar atualizacoes aprovadas da branch prod

[Timer]
OnBootSec=2min
OnUnitInactiveSec=2min
RandomizedDelaySec=15s
Persistent=true
Unit=vitta-one-prod-deploy.service

[Install]
WantedBy=timers.target
UNIT

systemctl daemon-reload
systemctl enable --now vitta-one-prod-deploy.timer
systemctl list-timers --all vitta-one-prod-deploy.timer --no-pager

echo 'CD instalado. Nenhuma credencial GitHub foi necessária.'
echo 'O Reflex atual não foi reiniciado durante a instalação.'
