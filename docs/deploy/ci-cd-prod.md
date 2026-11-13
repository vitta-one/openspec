# CI/CD do Vitta One — branch prod → VPS

## Objetivo e contexto

- Repositório: `vitta-one/openspec`; desenvolvimento na `develop` e promoção controlada para `prod`.
- Runtime existente: Reflex 0.9.10.post2, Python 3.12, PostgreSQL externo (Aiven), serviço `vitta-one.service`, Nginx Docker em `vitta.salles.dev.br`.
- Não altera o proxy, o DNS, o banco, os outros containers ou `/etc/vitta-one/vitta-one.env`.
- Sem secrets no GitHub: o GitHub **não** conecta à VPS por SSH. O agente local da VPS consulta commits públicos e a API pública de Actions.
- Publicação é automática **após o SHA da branch prod obter CI verde**, com verificação periódica (aprox. 2 minutos após cada verificação concluída).

## Arquitetura

1. PR para `develop`: o workflow `.github/workflows/production-ci.yml` executa validação de OpenSpec strict, PostgreSQL 16 descartável, migrations, Pytest, compilação e smoke de produção Reflex. O QA Chromium existente permanece independente.
2. PR de promoção `develop → prod` após revisão e checks obrigatórios. Push em `prod` executa o mesmo CI no SHA publicado.
3. O `vitta-one-prod-deploy.timer` consulta `origin/prod` e a conclusão do workflow `production-ci.yml` no GitHub Actions (evento `push`, mesmo SHA).
4. Após CI verde, constrói nova release isolada em `/srv/vitta-one-releases/<SHA>`, testa compilação e compara a revisão Alembic com o schema atual.
5. A troca de `/srv/vitta-one-current` é atômica; o serviço Reflex é reiniciado. O agente confirma HTTP local e HTTPS com certificado válido.
6. Se o health check falhar, restaura a release anterior, reinicia o serviço e bloqueia novas tentativas **daquele SHA**. Um novo commit em `prod` permite nova tentativa.

As credenciais ficam **exclusivamente** em `/etc/vitta-one/vitta-one.env` na VPS. O CI usa `vitta_one_test` sintético e não conhece o Aiven.

## Pré-requisitos de segurança

- A conexão HTTP/HTTPS já deve funcionar em `vitta.salles.dev.br` e o serviço `vitta-one` deve estar ativo.
- O checkout pré-existente `/srv/vitta-one` precisa conter `.git` e pertencer a `vitta-one`.
- O código deve estar na `develop` aprovada antes de promover para `prod`.
- Configure no GitHub **Settings → Rules → Rulesets** para `prod`: exigir PR, status obrigatório do job `OpenSpec, migrations QA, Pytest, Reflex e smoke`, bloquear force-push e exclusão, restringir quem pode fazer push. Sem proteção de branch, pessoas autorizadas a dar push em `prod` também poderiam alterar o próprio CI.
- O fluxo só funciona sem credenciais GitHub enquanto o repositório e os resultados de Actions estiverem acessíveis publicamente.
- Recomendado desativar `VITTA_ONE_LOCAL_ADMIN_PREVIEW` em produção; o agente recusa implantar se estiver em `true`.
- O serviço roda código como `vitta-one`; o instalador e o agente de publicação usam privilégios administrativos apenas para alternar releases e reiniciar a unidade.

## Instalação única na VPS

**Esta etapa é indispensável:** a edição do GitHub sozinha não consegue instalar serviços numa VPS que não tem conexão de administração remota vinculada. Nenhum token, chave SSH ou senha de banco precisa ser fornecido nem inserido no GitHub.

Depois de integrar a PR de infraestrutura à `develop`, na VPS já autenticada:

```bash
cd /root/apps/vitta-one
git status -sb
git pull --ff-only origin develop
bash scripts/deploy/bootstrap-vps.sh
systemctl list-timers --all vitta-one-prod-deploy.timer
```

O bootstrap instala `vitta-one-prod-deploy.service`, `vitta-one-prod-deploy.timer` e o override do serviço Reflex sem reiniciar imediatamente a versão atual.

Após a aprovação, promova a mesma versão para `prod` (PR de `develop` para `prod`); quando o CI desse commit passar, o timer da VPS detectará e publicará a release.

## Operação e observabilidade

```bash
systemctl status vitta-one --no-pager
systemctl status vitta-one-prod-deploy.timer --no-pager
journalctl -u vitta-one-prod-deploy.service -n 80 --no-pager
cat /var/lib/vitta-one-deploy/current.sha
curl -fsSL https://vitta.salles.dev.br/login -o /dev/null
```

Para iniciar uma verificação imediata **depois de configurar** o timer:

```bash
systemctl start vitta-one-prod-deploy.service
```

Para suspender implantações automáticas (sem interromper a aplicação atual):

```bash
systemctl disable --now vitta-one-prod-deploy.timer
```

## Schema, falhas e limites

- **Migrations novas não são aplicadas automaticamente ao Aiven.** Se o schema não estiver na mesma revisão das migrations da nova release, o deploy falha fechado. Analise a migration, plano de backup e impacto antes de aplicá-la por procedimento separado. Isso protege prontuários e informações clínicas de mudanças não revisadas.
- Rollback cobre apenas **código**, não o schema do banco. Sem downgrade automático.
- Falha no CI, indisponibilidade do GitHub, erro de build ou de validação não alteram o serviço em execução.
- Um restart de Reflex causa indisponibilidade breve; não é deploy sem downtime. Sessões WebSocket podem reconectar.
- O GitHub Actions não prova funcionamento de login real: após a primeira publicação, homologue login, permissões, WebSocket, recepção, agenda e prontuário com dados sintéticos.
- Se o repositório deixar de ser público, substitua a consulta não autenticada por uma integração segura com credenciais gerenciadas, sem colocar tokens no código.
