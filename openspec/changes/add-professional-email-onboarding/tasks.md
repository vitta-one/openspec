## Domínio e dados
- [ ] Migration segura para credencial temporária e status do e-mail.
- [ ] Serviço de cadastro transacional com e-mail normalizado, unique e ID interno.
- [ ] Reutilização segura de Médico existente e duplicidade proibida.
- [ ] Testes de concorrência e de rollback.

## Resend
- [ ] Adaptador com timeout, status seguro e headers oficiais.
- [ ] Envio de senha inicial sem persistência em claro.
- [ ] Mensagens honestas de não configurado/falha/aceito/indeterminado.
- [ ] Recuperação administrativa segura para falha de convite.
- [ ] Testes de rede sem envios reais.

## Auth e interface
- [ ] Bloquear todas as capabilities de role até troca obrigatória.
- [ ] Implementar rota protegida de troca e expiração.
- [ ] Formulário Administrador reduzido a nome/e-mail/especialidades.
- [ ] Tela de status, feedback, loading e erros acessíveis.

## QA
- [ ] Testar role, sessão, expirado, duplicidade, concorrência, timeouts.
- [ ] OpenSpec strict + Pytest PostgreSQL16 + Reflex compile.
- [ ] Browser QA incluindo viewports estreitos.
- [ ] Revisar diffs, evidências e só então sync/archive.
