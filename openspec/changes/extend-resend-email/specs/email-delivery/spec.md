# Spec Delta — Entrega de e-mails

## Purpose

Rastrear intenções e tentativas de envio ao Resend com estados verdadeiros, controle de concorrência, verificação de webhooks e recuperação operacional segura.

## ADDED Requirements

### Requirement: Intenção única e tentativas rastreáveis
O sistema MUST registrar intenção antes de enviar, com tipo, referência de evento, destinatário elegível, provedor e estado. MUST impedir intenção duplicada por evento/destinatário e processamentos simultâneos da mesma intenção. Tentativas MUST ter identificador estável e resultado persistido, sem armazenar mensagem integral ou segredo.

#### Scenario: Evento concorrente
- **WHEN** dois consumidores solicitam comunicação para o mesmo evento e destinatário
- **THEN** existe uma intenção e no máximo uma tentativa externa em andamento.

#### Scenario: Reinício do consumidor
- **GIVEN** tentativa estava em andamento e o processo termina antes de gravar resposta
- **WHEN** o consumidor reinicia
- **THEN** a tentativa passa a resultado desconhecido e não é reenviada automaticamente.

### Requirement: Estado de envio corresponde à evidência
O sistema MUST distinguir PENDING, SENDING, ACCEPTED, DELIVERED, FAILED, UNKNOWN, NOT_CONFIGURED e SUPPRESSED. HTTP válido com id do provedor MUST produzir ACCEPTED, nunca DELIVERED. Timeout, resposta inválida ou interrupção incerta MUST produzir UNKNOWN. Entrega MUST exigir confirmação autêntica do provedor e MUST NOT prometer chegada à caixa de entrada.

#### Scenario: Confirmação por e-mail
- **GIVEN** Consulta reservada e destinatário elegível
- **WHEN** evento autorizado solicita confirmação e Resend aceita com id
- **THEN** registra ACCEPTED e id, impedindo duplicação para o mesmo evento.

#### Scenario: Falha no Resend
- **GIVEN** e-mail solicitado
- **WHEN** API apresenta timeout
- **THEN** registra UNKNOWN, não informa entrega e não efetua reenvio automático cego.

#### Scenario: Rejeição e resposta incompleta
- **WHEN** provedor retorna rejeição HTTP ou sucesso sem id válido
- **THEN** registra respectivamente FAILED ou UNKNOWN com código seguro e sem corpo da resposta.

### Requirement: Idempotência local durável e reenvio autorizado
O sistema MUST manter deduplicação local além da janela externa de 24 horas. Tentativa MUST usar chave Resend estável. Reenvio manual MUST exigir motivo, elegibilidade atual e autorização: Administrador para acesso médico; Recepcionista para convite/agenda; Administrador ou Financeiro para evento financeiro. UNKNOWN MUST exigir consulta/revisão antes de nova emissão; ACCEPTED/DELIVERED MUST NOT permitir reenvio ordinário.

#### Scenario: Repetição após 24 horas
- **WHEN** evento já aceito reaparece após expirar idempotência externa
- **THEN** deduplicação local impede novo envio.

#### Scenario: Reenvio não autorizado
- **WHEN** identidade sem permissão solicita retry diretamente
- **THEN** nega antes de criar tentativa ou acessar dados da mensagem.

#### Scenario: Falha revisada
- **GIVEN** falha definitiva e destinatário ainda elegível
- **WHEN** operador autorizado confirma reenvio com motivo
- **THEN** cria tentativa auditável, sem duplicar a intenção original; acesso com segredo exige reemissão pelo fluxo existente.

### Requirement: Webhook Resend autenticado e resistente a replay
O sistema MUST verificar assinatura Svix sobre os bytes originais e validar timestamp antes de atualizar entrega. MUST deduplicar pelo identificador autenticado, vincular pelo id da mensagem enviada e tolerar eventos fora de ordem sem regredir entrega confirmada para aceitação. Eventos não vinculados MUST permanecer para revisão sem alterar outra mensagem.

#### Scenario: Entrega confirmada
- **GIVEN** mensagem ACCEPTED com id conhecido
- **WHEN** webhook email.delivered possui assinatura e timestamp válidos
- **THEN** registra DELIVERED uma única vez com evidência do provedor.

#### Scenario: Assinatura inválida ou replay antigo
- **WHEN** corpo foi adulterado, assinatura falta ou timestamp excede tolerância de 5 minutos
- **THEN** rejeita sem atualizar notificação.

#### Scenario: Falha posterior e duplicidade
- **WHEN** evento autêntico de bounce/failure chega ou é repetido
- **THEN** registra falha de entrega e bloqueia novos envios automáticos ao endereço afetado; não duplica tentativa.

#### Scenario: Evento chega antes da resposta de envio
- **WHEN** id do provedor ainda não foi associado localmente
- **THEN** conserva evento autenticado mínimo e tenta vincular depois, sem descartá-lo como entrega inexistente.
