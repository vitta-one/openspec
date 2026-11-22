# Tasks — Assinatura de prescrições

## Explore e Review
- [ ] Aprovar momento de congelamento, formato/versionamento e autorização do signatário.
- [ ] Revisar API/webhooks, estados, Sandbox, autenticação e limites reais da ZapSign.
- [ ] Revisar alterações necessárias em clinical-prescription e validar change OpenSpec strict.

## Apply (não iniciado)
- [ ] Criar entidades e migrations aditivas com trilha de eventos e idempotência em QA isolado.
- [ ] Implementar snapshot protegido e bloqueio/versionamento de prescrição durante assinatura.
- [ ] Implementar adaptador ZapSign Sandbox com timeouts, estado indeterminado e reconciliação.
- [ ] Integrar webhook autenticado e processamento durável.
- [ ] Integrar UI/State Reflex e estados de assinatura sem afirmar conclusão indevida.
- [ ] Implementar testes de segurança, concorrência, duplicidade, ordem de eventos e falha externa.

## Verify e Archive
- [ ] Executar OpenSpec strict, Pytest, migration QA, Reflex compile e Chromium.
- [ ] Homologar fluxo ZapSign Sandbox com documentos sintéticos e registrar evidências.
- [ ] Revisar diff e sincronizar contrato consolidado somente após aceite.
