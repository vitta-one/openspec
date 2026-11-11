# Auditoria Asaas e Resend — 11/11/2026

## Evidência e limites

Base: repositório privado `vitta-one/openspec`, branch `develop`, commit `156b0a6a1b811b355af046d296ebe38c5fff7079`. Clone separado em `vitta-one/`, sem modificar o trabalho anterior da pasta hospedeira. Auditoria estática de fontes, modelos, serviços, migrations, testes, specs consolidadas e propostas das 22 changes ativas. Não é evidência de execução funcional. OpenSpec instalado: 1.14.1; skills gerados pela versão 1.13.0; schema `spec-driven`.

## Diagnóstico e matriz de reaproveitamento

| Área | Implementação observada | Reaproveitar | Lacuna |
|---|---|---|---|
| Financeiro | `ui/pages.py:finance_page` é shell protegido | shell, RBAC, tokens visuais | todo o domínio/persistência/projeções financeiras |
| Admin financeiro | `admin_finance_preview_page` usa `admin_preview_workspace`; `finance_preview` informa ausência de indicadores | composição e guard local QA | leitura financeira real e decisão sobre promoção da rota |
| Pacientes | `models/patient_queue.py:Patient`: nome, CPF único, telefone, `user_id` opcional | identidade/validação de CPF e vínculo com conta | vínculo cliente Asaas; paciente não tem e-mail próprio na tabela |
| Consultas | `models/appointment.py:Consultation` liga paciente, profissional, horário e ciclo clínico | FK e reserva transacional existentes | valor/tabela de preços não existem; cobrar exige regra explícita |
| Agenda | `appointment_scheduling/service.py` faz commit em reserva, reagendamento e cancelamento | locks, validações, `ConsultationScheduleChange` | inserir intenção de notificação na mesma transação antes de commit |
| Médico | `professional_directory/service.py` cria conta e profissional, senha temporária com hash/24h | criação/reemissão e autorização administrativa | registro compartilhado de metadados de tentativa |
| Resend | `professional_directory/email_sender.py` usa httpx, timeout 10s, escape HTML e chave de tentativa aleatória | contratos públicos `EmailDelivery`, dois senders | transporte duplicado; sem outbox geral/webhook de entrega |
| Portal | `patient_portal/service.py` valida consentimento, código hash, expiração 24h, revoga anterior e limita reenvio em 2 min | fluxo completo e `PatientPortalInvitation` | consentimento específico para novas comunicações |
| Autorização | `auth/authorization.py`: resolve sessão, exige role exata e troca inicial | validações por operação | guard financeiro multi-role sem ampliar guard clínico |
| Backend HTTP | `patient_portal/activation_api.py`: Starlette por `rx.App(api_transformer=activation_api)` | composição de rotas no backend Reflex | inbox Asaas e webhook Resend verificado |
| Banco | 14 revisions Alembic, cadeia única até `e9d3a8c2b170`; `target_metadata=None` em env.py | migrations explícitas e aditivas | modelos novos registrados no pacote; não confiar em autogenerate |
| Testes | suites de auth, agenda, onboarding, portal, clínico; PostgreSQL condicionais a DATABASE_URL | fixtures e contratos existentes | contratos Asaas, outbox, assinatura, concorrência financeira, E2E financeiro |

As buscas abrangeram código, modelos, serviços, migrations e specs, além de telas; não se inferiu ausência apenas por não haver interface. Não foram encontrados modelos, migrations ou chamadas Asaas implementados nessa base. A prévia financeira já evita dados demonstrativos: não há números mockados que precisem ser removidos nessa seção.

## Roles e divergências de especificação

O código possui ADMINISTRADOR, RECEPCIONISTA, MEDICO, FINANCEIRO e PACIENTE, embora a spec consolidada `access-control` ainda descreva quatro roles da fundação. Não remover PACIENTE nem criar role nova. Preservar permissões de serviços clínicos. Administrador não deve obter permissão de Recepção por ganhar operações financeiras.

`CONFIRMADA` representa chegada/check-in no ciclo atual, não a reserva. Proposta: confirmação de reserva em AGENDADA e nenhum envio adicional no check-in. Regras clínicas continuam iguais. `ACCEPTED` no sender é somente aceitação HTTP. Credencial temporária médica por e-mail é comportamento legado sensível a preservar; a instrução de não expor credenciais aplica-se a logs/UI/persistência, e não pode apagar silenciosamente esse fluxo existente. Não generalizar esse conteúdo para mensagens comuns.

## Changes ativas e sobreposições

| Grupo / changes | Interseção | Estratégia |
|---|---|---|
| `2026-10-31-separate-patient-registration-portal` | convite, consentimento e UI de paciente | preservar intervalo, código e contratos; preferência nova separada |
| `2026-10-31-unify-staff-registration`, `2026-10-31-fix-professional-registration-modal`, `refactor-admin-profissionais-20261031` | onboarding, status de envio e criação médica | manter assinaturas, reemissão e metadados atuais |
| `2026-10-31-reception-booking-modal`, `reception-patient-operational-profile`, `2026-10-31-refine-reception-agenda-checkin`, `reception-operacao-do-dia-20261031` | eventos de agenda/check-in e serviços com commit interno | hooks no serviço reutilizado, não duplicar nos States |
| `refine-global-navigation-20261031`, `2026-10-31-refine-admin-hub-navigation` | sidebar, rotas QA, auth State | editar somente destino financeiro após aprovação; preservar restantes |
| `refine-admin-reception-qa-panel`, `admin-qa-agenda-visual`, `2026-10-31-admin-qa-patient-dossier` | componentes de preview e guards | não relaxar flag de outros previews |
| `2026-10-31-manage-clinic-configuration` | cabeçalho institucional, cabeça de migration | usar marca/config existente; revalidar Alembic heads |
| `admin-horarios-calendario-operacional`, `reception-queue-operational-board-20261031` | concorrência de horários/fila | não modificar locks nem estados clínicos |
| `reception-patient-directory-20261031`, `reception-patient-registration-ux` | Patient e apresentação cadastral | não adicionar e-mail duplicado ao paciente; contato via conta vinculada |
| `2026-10-31-refine-employee-directory`, `2026-10-31-refine-employee-detail`, `2026-10-31-refine-specialty-management`, `refinar-modais-especialidades-20261031` | módulos UI compartilhados, sem regra financeira | não alterar diretórios/modais ou encerrar suas tasks |

Nenhuma change ativa tem proposta de financeiro Asaas. Há 22 changes em progresso com verificações pendentes; não arquivá-las nem declarar seu comportamento consolidado por inferência. Contratos novos serão adicionados em capabilities próprias; eventual mudança de contrato existente exige delta apropriado antes de Apply.

## Dependências externas verificadas

Consultadas em 11/11/2026, somente fontes oficiais:

- [Asaas autenticação](https://docs.asaas.com/docs/authentication-2): base Sandbox `https://api-sandbox.asaas.com/v3`, header `access_token`, User-Agent identificável.
- [Clientes](https://docs.asaas.com/reference/create-new-customer): POST `/customers`, `name`, `cpfCnpj`, `externalReference`; API permite duplicados e recomenda consulta antes de repetir resultado incerto.
- [Cobranças](https://docs.asaas.com/reference/create-new-payment): POST `/payments`, `customer`, `billingType`, `value`, `dueDate`; criação não prova recebimento.
- [Pix](https://docs.asaas.com/docs/payments-via-pix-or-dynamic-qr-code): GET `/payments/{id}/pixQrCode`, retorno de imagem, payload e validade.
- [Recebimento de eventos](https://docs.asaas.com/docs/receive-asaas-events-at-your-webhook-endpoint): validar `asaas-access-token`, deduplicar id, persistir antes de responder 200, processar separadamente.
- [Eventos financeiros](https://docs.asaas.com/docs/payment-events): CONFIRMED não é RECEIVED; estados de estorno são distintos.
- [Estorno](https://docs.asaas.com/reference/refund-payment): POST `/payments/{id}/refund` suporta Pix/cartão; saldo insuficiente pode impedir operação. Boleto não será homologado por esse endpoint.
- [Resend idempotência](https://resend.com/docs/dashboard/emails/idempotency-keys): chave externa conservada 24h; deduplicação local deve ser durável.
- [Resend assinatura](https://resend.com/docs/webhooks/verify-webhooks-requests): bytes originais, headers svix-id/timestamp/signature e secret próprio.

## Ambiente e próximos passos

OpenSpec disponível e repositório acessível. Não existe `.venv` no clone, `python` aponta para alias Windows sem runtime e `py -0p` não encontra instalações. `uv`, Docker e psql não foram encontrados no PATH. As variáveis DATABASE_URL, ASAAS_API_KEY, ASAAS_WEBHOOK_TOKEN, RESEND_API_KEY, RESEND_FROM_EMAIL e RESEND_WEBHOOK_SECRET não estão definidas no processo inspecionado; isso não prova ausência em outros ambientes. Não ler/exibir segredos de outros projetos.

Instalar runtime isolado e dependências é preparação necessária para Verify. PostgreSQL de teste e credenciais Sandbox/remetente/destinatário autorizado continuam necessários para homologação real. Não declarar mocks como Sandbox e não arquivar changes sem evidências exigidas.
