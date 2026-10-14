## Domínio e dados
- [x] Migration segura para credencial temporária e status do e-mail.
- [x] Serviço de cadastro transacional com e-mail normalizado, unique e ID interno.
- [x] Reutilização segura de Médico existente e duplicidade proibida.
- [x] Testes de concorrência e de rollback.

## Resend
- [x] Adaptador com timeout, status seguro e headers oficiais.
- [x] Envio de senha inicial sem persistência em claro.
- [x] Mensagens honestas de não configurado/falha/aceito/indeterminado.
- [x] Recuperação administrativa segura para falha de convite.
- [x] Testes de rede sem envios reais.

## Auth e interface
- [x] Bloquear todas as capabilities de role até troca obrigatória.
- [x] Implementar rota protegida de troca e expiração.
- [x] Formulário Administrador reduzido a nome/e-mail/especialidades.
- [x] Tela de status, feedback, loading e erros acessíveis.

## QA
- [x] Testar role, sessão, expirado, duplicidade, concorrência, timeouts.
- [x] OpenSpec strict + Pytest PostgreSQL16 + Reflex compile.
- [x] Browser QA incluindo viewports estreitos.
- [x] Revisar diffs, evidências e só então sync/archive.

### Evidência de encerramento (2026-10-14)

- Código integrado à `develop` via PR #305.
- Gates automatizados: OpenSpec 10/10, Pytest 179 aprovados em PostgreSQL 16 descartável; Chromium com viewports 320/375/768 e fluxos de diretório/primeiro acesso/agenda.
- Requisitos sincronizados com `openspec/specs/` antes do arquivamento.
- Integração de e-mail real e homologação manual do Hackintosh são verificações de ambiente separadas, não comprovadas por estes testes.
