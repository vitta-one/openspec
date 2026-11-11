# Design — Comunicação Resend

## Context

Ver proposal e auditoria. Sender atual tem dois transportes iguais, timeout, HTML escapado e UNKNOWN em erro de rede. Portal gera código em memória e persiste somente hash. Médico usa senha temporária em memória e persiste hash. Não colocar esses segredos numa outbox com conteúdo completo.

## Goals / Non-Goals

**Goals:** preservar API atual, persistir estado verificável e adicionar notificações com outbox transacional. **Non-Goals:** fila externa, recuperação de senha sem fluxo, migração do onboarding para um novo sistema de credenciais ou envio de dado clínico.

## Decisions

### 1. Adaptador compartilhado compatível

Extrair transporte httpx em `notifications/resend.py`, mantendo `EmailDelivery` importável e funções públicas atuais como wrappers. Timeout explícito até 10s, redirects desativados e endpoint fixo `https://api.resend.com/emails`. Chaves só no backend. `Idempotency-Key` persistida para nova tentativa, sem token/secreto na chave. Resposta com id válido = ACCEPTED; erro de rede/resposta ambígua = UNKNOWN; rejeição confirmada = FAILED. Não registrar request/response bodies. Alternativa SDK adicional rejeitada para transporte por já existir httpx.

Onboarding continua síncrono no trecho em que segredo existe: registrar intenção/tentativa antes do envio, enviar uma vez, atualizar metadados. Se crash após registrar SENDING, marcar UNKNOWN ao recuperar, exigindo reemissão de segredo pelo fluxo original. Nunca reconstituir segredo perdido de armazenamento. Manter status legados nos registros existentes para compatibilidade e associar message id à tentativa.

### 2. Persistência mínima

| Entidade | Campos propostos | Integridade |
|---|---|---|
| NotificationPreference | paciente, agenda_enabled, financial_enabled, changed_by, changed_at | paciente UNIQUE, FK RESTRICT; default false |
| EmailNotification | tipo, referência/revisão do evento, patient/professional quando aplicável, chave de destinatário, estado, datas | UNIQUE evento + destinatário; sem corpo HTML, código ou senha |
| EmailAttempt | notificação, sequência, idempotency key UUID, estado, provider=resend, message id, código de erro seguro, timestamps | UNIQUE notificação + sequência; chave/message id UNIQUE quando presentes |
| EmailWebhookEvent | svix id, tipo, email id, timestamp, estado de vínculo/processamento | svix id UNIQUE; sem corpo integral |
| EmailRetryRequest | notificação, autor, motivo, revisão de incerteza e data | auditoria durável de cada solicitação manual |

Chave de destinatário é hash do e-mail normalizado no registro da intenção, com resolução do endereço em User/Invitation no envio; não duplicar endereço em várias tabelas. Troca de contato invalida intenção antiga e exige evento autorizado novo. Associar preferências à conta/paciente com autorização server-side; não assumir consentimento de ativação como permissão geral. Auditoria de alteração conserva antes/depois e autor em registro de eventos de preferência, ou estrutura equivalente na mesma entidade de auditoria de notificação; escolher uma representação sem perder histórico.

### 3. Templates e minimização

`notifications/templates.py`: layout HTML de largura flexível máxima 600 px, texto puro paralelo, português, links descritivos e valores escapados (`html.escape` para texto/atributos). Campos tipados/whitelist por tipo; não aceitar HTML pronto do navegador nem dict clínico irrestrito. Templates de acesso mantêm texto de expiração; eventos de agenda mostram somente data/hora local e clínica; financeiros mostram valor/vencimento e link hospedado validado. Validar URL pública da configuração e links Asaas por HTTPS/origem permitida, sem credencial em URL. Não inventar documento de recibo.

### 4. Atomicidade e worker

Inserir intenção de agenda antes dos commits de schedule/reschedule/cancel no serviço compartilhado, para cobrir Recepção e portal sem duplicar eventos nos States. Revisão usa identidade persistida da alteração, não relógio do navegador. Confirmação da reserva AGENDADA é o gatilho aprovado; check-in CONFIRMADA não envia segunda mensagem.

Worker resolve intenção + referência, confirma preferência/contato/situação, bloqueia intenção com `FOR UPDATE SKIP LOCKED`, cria tentativa SENDING e faz commit antes de HTTP. Após resposta atualiza tentativa. Lease vencido de tentativa de envio vira UNKNOWN e nunca PENDING automático; assim não há reenvio cego após crash. GET de consulta ao provedor pode esclarecer resultado; retry manual só após resultado revisado e autorização. Deduplicação local não expira com as 24h da chave externa. Nenhuma dependência de `rx.background` em memória para entrega durável.

Lembretes: scheduler/CLI a cada 5 min busca 23h ≤ scheduled_at-now ≤ 24h, chave `(reminder, consultation_id, schedule_revision, recipient)`. No envio, conferir revisão atual, status AGENDADA/CONFIRMADA e janela; suprimir se cancelada, reagendada, sem preferência ou atrasada. Não enviar backlog antigo quando habilitar nova funcionalidade; registrar instante de ativação e elegibilidade somente de eventos novos. Integração financeira consome histórico de transição persistido; evitar dependência circular entre módulos.

### 5. Assinatura e rastreamento

POST proposto `/api/webhooks/resend` junto à API Reflex existente. Verificar assinatura Svix com biblioteca oficial Python (dependência dedicada apenas para verificação criptográfica) sobre bytes originais, `svix-id`, `svix-timestamp`, `svix-signature` e RESEND_WEBHOOK_SECRET; tolerância 5 min e body limitado 256 KiB. Secret não é API key. Autenticar antes de decodificar/aplicar, deduplicar svix id; evento antes de id associado permanece pendente.

| Evidência | Estado |
|---|---|
| Intenção criada | PENDING |
| Tentativa persistida iniciada | SENDING |
| POST aceito com id | ACCEPTED |
| email.delivered autêntico | DELIVERED (entrega ao servidor destinatário, não promessa de inbox) |
| email.bounced / email.failed | FAILED, com dimensão de falha de entrega preservada |
| email.complained | SUPPRESSED para comunicações futuras; preservar evidência anterior |
| Timeout ou crash incerto | UNKNOWN |
| Configuração ausente | NOT_CONFIGURED |
| Destinatário/revisão/preferência inelegível | SUPPRESSED |

Histórico de eventos é separado do status agregado para não apagar bounce/reclamação posterior nem regredir DELIVERED para ACCEPTED por ordem de chegada. Webhook só altera message id conhecido, e eventos não vinculados não criam mensagem nova. Não registrar segredos na exceção da biblioteca.

### 6. Acesso e operação

API administrativa de reenvio é operação Python autorizada chamada pelo State, sem endpoint público mutante. Administrador reemite acesso médico; Recepcionista convite/agenda; Administrador/Financeiro comunicações financeiras. Para UNKNOWN, consulta/revisão e confirmação do operador antes de nova tentativa; ACCEPTED/DELIVERED bloqueiam reenvio normal. Rate limit do convite atual de 2 min preservado. Preferências podem ser alteradas pelo próprio paciente ou Recepção com confirmação explícita; guardar finalidade/autor e revogação.

## Risks / Trade-offs

- [Sem contato em Patient] → usar conta vinculada, suprimir paciente sem conta em novos eventos; convites continuam com destinatário próprio já validado.
- [Falha entre envio e commit] → UNKNOWN; não garantir entrega exatamente uma vez em sistemas distribuídos.
- [Retenção ainda não definida] → guardar apenas metadados mínimos, sem purga automática; política de retenção deve ser aprovada antes de coletar produção.
- [Preferências novas] → padrão false; não migrar convites como opt-in geral.
- [Capacidade operacional do worker] → documentar comando, intervalo, backlog e procedimentos UNKNOWN; teste de reinício obrigatório.

## Migration Plan

Migration aditiva autônoma, sem FKs obrigatórias em tabelas financeiras para permitir instalação independente. Revalidar cabeça Alembic e encadear com financeira ao integrar. Existing convites/profissionais preservados; registros históricos não são convertidos em novas intenções enviáveis. Upgrade/downgrade apenas em PostgreSQL descartável. Rollback desativa worker/gatilhos e conserva metadados.

## Revisão e decisões

Na continuação da verificação, alinhar os seletores E2E de onboarding aos campos comuns do cadastro unificado já existente, mantendo os cenários de criação, estado de envio ausente e bloqueio de e-mail duplicado. Asserções devem usar a interface atual e continuar verificando persistência e ausência de falsa entrega. Os fluxos reais Resend permanecem pendentes de credenciais.

Em 11/11/2026 usuário aprovou novos gatilhos com autorização de comunicação registrada, lembrete 24h, confirmação na reserva e exclusão temporária de recuperação de senha/cartão. Janela de tolerância de uma hora limita envios atrasados sem mudar antecedência nominal. Escolhas de assunto, espaçamento e ícone seguem o design system, sem afetar contrato. Nenhum envio real está autorizado sem destinatário de teste informado.
