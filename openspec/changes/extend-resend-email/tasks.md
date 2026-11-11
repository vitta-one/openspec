# Tasks — Comunicação Resend

## 1. Explore, Propose e Review

- [x] 1.1 Auditar sender, convites, credenciais, serviços de agenda e testes; conferir matriz no diagnóstico compartilhado.
- [x] 1.2 Criar proposta, três specs e design; verificar arquivos e validação strict da especificação.
- [x] 1.3 Registrar aprovação dos gatilhos, autorização de comunicação, lembrete e confirmação na reserva; conferir decisões de 11/11/2026.
- [x] 1.4 Revisar rastreabilidade, contratos oficiais, privacidade e conflitos; verificar relatório e `openspec validate extend-resend-email --strict --no-interactive`.

## 2. Transporte, templates e onboarding

- [x] 2.1 Extrair transporte compartilhado mantendo API pública de email_sender; testar configuração, timeout, rejeição, resposta inválida, ACCEPTED e ausência de retry cego.
- [ ] 2.2 Criar layout HTML/texto e templates aprovados; testar escape, URL, campos permitidos, leitura móvel e ausência de diagnóstico/recibo inventado.
- [x] 2.3 Registrar intenção/tentativa de acesso sem persistir segredo; executar regressões médicas, convite/ativação, expiração, reemissão e QA local.
- [x] 2.4 Atualizar documentação de configuração e limites; verificar compatibilidade das variáveis existentes e não anunciar recuperação de senha/cartão.

## 3. Persistência e autorização

- [x] 3.1 Criar modelos/migration de preferências, auditoria, notificação, tentativa e webhook mínimo; testar unicidade, FKs, valores e upgrade/downgrade isolado.
- [ ] 3.2 Implementar preferências revogáveis separadas e UI nos fluxos existentes do paciente/Recepção; testar titularidade, role, confirmação explícita e padrão false.
- [x] 3.3 Implementar reenvio manual com motivo e elegibilidade; testar permissões por tipo, ACCEPTED/DELIVERED bloqueados e UNKNOWN exigindo revisão.

## 4. Outbox e eventos

- [x] 4.1 Implementar processamento de intenção com lease e tentativa antes do HTTP; testar dois workers, reinício/crash, UNKNOWN e deduplicação além de 24h.
- [x] 4.2 Integrar reserva/reagendamento/cancelamento antes do commit compartilhado; testar Recepção e portal, rollback, corrida de horário e ausência de envio no check-in.
- [x] 4.3 Implementar scheduler de lembrete a cada 5 minutos e revisão de horário; testar janela 24h–23h, cancelamento, reagendamento, atraso e concorrência.
- [x] 4.4 Consumir cobrança disponível/primeiro RECEIVED com autorização financeira; testar duplicados, ausência/revogação de preferência e falha do Resend sem rollback financeiro.
- [ ] 4.5 Documentar worker, elegibilidade e revisão de falhas; executar comandos documentados no teste isolado.

## 5. Entrega e privacidade

- [x] 5.1 Integrar webhook com verificação Svix oficial e limite de corpo na API Reflex; testar assinatura válida/inválida, replay, secret ausente e JSON adulterado.
- [ ] 5.2 Vincular eventos por message id com deduplicação; testar entrega, bounce, complaint, evento anterior à resposta e ordem invertida.
- [x] 5.3 Verificar logs, banco e State em falhas/acesso negado; comprovar ausência de segredo, corpo HTML e dados clínicos.

## 6. Verify integrado

- [x] 6.1 Executar testes existentes de acesso/agenda/onboarding/portal e contratos novos; registrar aprovados/falhas/skips reais.
- [x] 6.2 Exercitar concorrência, outbox, preferências e reinício em PostgreSQL; registrar evidências sem inferir suporte pelo SQLite.
- [ ] 6.3 Executar `reflex compile --dry` e E2E de preferências → evento → tentativa → entrega simulada, em desktop/mobile.
- [ ] 6.4 Validar Resend real com remetente verificado, destinatário de teste explicitamente autorizado e webhook assinado; separar aceitação de entrega.
- [x] 6.5 Comparar implementação/specs, validar OpenSpec strict e preparar PR com resultados e pendências.

## Workflow follow-up

- Arquivar pelo procedimento oficial somente após todas as tarefas verificadas; manter change ativa enquanto faltar homologação ou houver falha crítica.
- Sincronizar specs sem antecipar escrita em `openspec/specs/` e preservar histórico existente.

## Evidência local e pendências

Ver `docs/implementacao-asaas-resend-evidencias-2026-11-11.md`. Implementação local adicionada e compilada; tasks com verificações específicas ainda não executadas permanecem abertas. PostgreSQL e homologação real dependem do ambiente configurado; não interpretar os testes simulados como Sandbox real.

PostgreSQL: CI `43062255648`, commit `6d0b941`, aprovou concorrência de dois consumidores com um único envio, recuperação SENDING → UNKNOWN sem repetição, preferências e auditoria de reenvio; 537 testes aprovados, 2 skips na suite integral. Esses envios usam transporte simulado.
