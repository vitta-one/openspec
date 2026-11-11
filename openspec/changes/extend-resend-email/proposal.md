# Proposal — E-mails transacionais Resend

## Why

O adaptador Resend já envia credenciais médicas e convites do portal, mas duplica transporte e não oferece outbox compartilhada nem rastreamento de entrega. Novas notificações precisam preservar esses fluxos e distinguir aceitação HTTP de entrega confirmada pelo provedor.

## What Changes

- Objetivo: infraestrutura compartilhada de transporte, templates responsivos, registro seguro de intenções/tentativas e deduplicação por evento.
- Manter as assinaturas públicas de `professional_directory/email_sender.py` e a expiração de 24 horas de credenciais/convites.
- Registrar metadados de envios de acesso sem persistir senhas, códigos, tokens, HTML ou corpo da mensagem.
- Implementar confirmação da reserva, reagendamento, cancelamento e lembrete de 24 horas, com autorização de comunicação específica aprovada pelo usuário.
- Consumir eventos financeiros após commit: cobrança disponível e pagamento efetivamente recebido.
- Verificar webhooks assinados Resend para rastreamento de entrega, falha e reclamação; aceitar requisição não significa entrega na caixa de entrada.
- Reenvio manual autorizado com motivo, identidade e revisão de elegibilidade; resultado incerto não dispara retry cego.

## Capabilities

### New Capabilities

- `transactional-email`: templates, privacidade, autorização e preservação do onboarding.
- `email-delivery`: outbox, tentativas, transporte, deduplicação e rastreamento por webhook.
- `appointment-email-notifications`: gatilhos e frequência de comunicação de agendamento.

### Modified Capabilities

Nenhuma: não muda a política de senha, ativação, agendamento ou atendimento; adiciona comunicação aos eventos autorizados. Reavaliar se a revisão exigir mudar o contrato de confirmação/check-in.

## Impact

- Reutilizar adaptador `httpx`, validadores de e-mail, `Patient.user_id → User.email`, convites e onboarding existentes.
- Adicionar módulo `vitta_one/notifications/`, persistência, worker, templates e testes; migração aditiva independente da financeira.
- Pontos compartilhados: serviços de agenda, ciclo de check-in, sender existente e `api_transformer` já usado por `activation_api` (Starlette integrada ao Reflex). Nenhum novo framework.
- Dependências: remetente verificado, `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `VITTA_ONE_PUBLIC_URL`; secret próprio de assinatura `RESEND_WEBHOOK_SECRET` para rastrear entrega. E-mails financeiros dependem dos eventos de `integrate-asaas-financial`; onboarding e agenda não dependem do Asaas.

## Fora do escopo

Marketing, anexos clínicos, recibo inventado, envio para contatos reais sem autorização e redefinição de senha pública (fluxo inexistente na autenticação atual). Template de recuperação só será criado junto de fluxo seguro aprovado; não criar botão/link sem funcionalidade. Não substituir a credencial temporária médica por outro fluxo nesta change.

## Riscos técnicos e de segurança

- Chave aleatória atual identifica tentativa, não deduplica evento de negócio; chave nova deve persistir por evento/tentativa apropriada.
- Resend mantém idempotência externa por 24 horas: unicidade local durável permanece necessária.
- Commit externo seguido de crash local gera estado incerto, nunca prova de falha definitiva.
- Consentimento de ativação não autoriza automaticamente notificações clínicas/financeiras. Nova preferência explícita e revogável é proposta para aprovação.
- Capturar assinatura sobre bytes originais; limitar corpo/replay; não registrar payload sensível. Retenção de metadados necessita política aprovada antes de purga.

## Estratégia de testes

Preservar `test_medical_email_onboarding.py` e testes do portal; adicionar contratos HTTP, escape HTML/URL, ausência de segredos, deduplicação concorrente, worker interrompido, webhook assinado/forjado e relógio controlado para lembretes. Compilar Reflex e validar E2E com correio de teste autorizado.

## Critérios de conclusão

Onboarding sem regressão; gatilhos aprovados implementados; nenhuma duplicidade; timeout = UNKNOWN; webhook verificado antes de marcar entrega; testes PostgreSQL/contrato/E2E com evidências; validação OpenSpec e arquivamento após todas as tasks verificadas.

## Decisões aprovadas em 11/11/2026

O usuário aprovou: novos eventos somente com autorização de comunicação registrada; confirmação, reagendamento, cancelamento, cobrança disponível e pagamento confirmado; lembrete 24 horas antes. A confirmação comunica a reserva `AGENDADA`, sem confundir com check-in `CONFIRMADA`. Um e-mail por evento/revisão; lembrete com janela operacional de 24h a 23h, sem recuperar atrasados. Aviso de vencimento permanece desativado. Recuperação de senha e cartão ficam pendentes de homologação. Preservar os envios de acesso existentes.
