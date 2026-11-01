## Implementação
- [x] Criar modelo singleton e migration aditiva com trilha de auditoria.
- [x] Centralizar a leitura banco → fallback e escrita autenticada com revisão.
- [x] Substituir aviso técnico por formulário de administração com validação e feedback.
- [x] Conectar portal às leituras persistidas.
- [x] Adicionar testes unitários de persistência, RBAC, validação, conflito e auditoria.

## Validação pendente de execução em ambiente QA/CI
- [ ] Executar migration em PostgreSQL 16 QA isolado e validar reversão apenas descartável.
- [ ] Executar Pytest e OpenSpec strict.
- [ ] Executar `reflex compile --dry`.
- [ ] Homologar Chromium/Playwright (320, 390, 768, 1024 e 1440px), teclado e regressão do portal.
- [ ] Revisar e arquivar change somente após aceitação e evidências.
