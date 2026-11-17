# Incidente: virtualenv de release não relocável — 17/11/2026

## Evidência e escopo

No servidor Vitta One, a aplicação pública permanecia ativa com
`/srv/vitta-one-current -> /srv/vitta-one`, mas o timer
`vitta-one-prod-deploy.timer` falhava a cada tentativa. O executável
`/srv/vitta-one-releases/3e69ca7d44fc799d05b44ef64807dc896636e8b2/.venv/bin/alembic`
existia, porém o seu shebang apontava para
`/srv/vitta-one-releases/.building-3e69ca7d44fc.IgUYFgRS/.venv/bin/python`,
um caminho temporário que não existia mais.

A causa era criar `.venv` no diretório `.building-*` e mover todo
o diretório para `/srv/vitta-one-releases/<SHA>`, invalidando os shebangs
absolutos dos executáveis instalados por pip. O marcador `.ready` havia
sido movido junto, de modo que a release incorreta parecia reutilizável.

## Correção proposta

- Extrair somente os arquivos de código em um diretório temporário e
  movê-los para `/srv/vitta-one-releases/<SHA>` **antes** de criar o venv.
- Criar `.venv` diretamente no caminho definitivo da release.
- Verificar o caminho absoluto do interpretador do Alembic e a
  executabilidade de seus comandos antes de aceitar uma release como pronta.
- Se uma release não ativa estiver incompleta ou tiver marcador inválido,
  movê-la para um caminho `.invalid-*` para diagnóstico, sem apagá-la.
- Manter a proteção da release ativa e o swap atômico com rollback;
  `.ready` é criado somente após a instalação, o check de schema e o compile.

O processo **não** executa `alembic upgrade head` automaticamente. O
`alembic current --check-heads` é um bloqueio intencional quando o banco
não está no schema esperado, e exige avaliação de migração e backup.

## Pré-requisitos para promover a produção — não executar sem autorização

1. Aprovar e mesclar esta correção em `develop`, após CI e revisão.
2. Revisar separadamente a promoção de `develop` para `prod`. A PR
   #354 já foi mesclada em `develop`; a PR #350 **não deve ser incluída**.
3. Executar validação e testes com PostgreSQL QA isolado, consultar as
   migrations exigidas pela release, fazer backup e obter autorização para
   qualquer migração ou deploy de produção.
4. Aguardar **CI de evento push na branch prod** concluída com sucesso no
   SHA exato. CI de PR/manual não habilita o deploy automático.

### Atualização única do agente instalado na VPS (somente após aprovação)

O agente em `/usr/local/libexec/vitta-one-deploy/poll-prod.sh` ainda contém
a implementação antiga. Ele só é atualizado automaticamente **após um deploy
bem-sucedido**, portanto é necessária uma atualização única e autorizada.

```bash
# Executar como root na VPS SOMENTE depois da promoção aprovada à prod.
runuser -u vitta-one -- git -C /srv/vitta-one fetch --no-tags origin \
  'refs/heads/prod:refs/remotes/origin/prod'
git -C /srv/vitta-one show origin/prod:scripts/deploy/poll-prod.sh \
  > /tmp/vitta-poll-prod-candidate.sh
bash -n /tmp/vitta-poll-prod-candidate.sh
# Antes de instalar: revisar o diff e garantir a CI verde do SHA de prod.
install -o root -g root -m 750 /tmp/vitta-poll-prod-candidate.sh \
  /usr/local/libexec/vitta-one-deploy/poll-prod.sh
# Acionar somente com autorização de deploy e backup validado:
systemctl start vitta-one-prod-deploy.service
```

Após a execução autorizada, verificar `journalctl -u
vitta-one-prod-deploy.service -n 100 --no-pager`,
`/var/lib/vitta-one-deploy/current.sha`, o destino de
`/srv/vitta-one-current`, a unidade `vitta-one.service`
e HTTP/HTTPS. **O SHA instalado, o link ativo e o processo em execução
devem corresponder à versão aprovada.**

Nunca remover volumes PostgreSQL ou apagar releases existentes para
forçar a implantação. O conserto do script não publica automaticamente
a PR #354, nem substitui uma migração de banco aprovada.
