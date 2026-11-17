## ADDED Requirements

### Requirement: Dashboard apresenta métricas agregadas de e-mails da agenda
A visão `/recepcao` MUST exibir contagens persistidas de notificações de agenda criadas nas 30 datas locais mais recentes, incluindo hoje: aceitas, entregues, falhas e pendentes/indeterminadas. Aceitação pelo Resend MUST ser distinguida de entrega confirmada. A projeção MUST exigir role Recepcionista no servidor e MUST retornar somente contagens, sem destinatários, conteúdo, identificadores de mensagens ou dados clínicos.

#### Scenario: Período sem notificações
- **WHEN** não há notificações de agenda criadas nas 30 datas locais mais recentes, incluindo hoje
- **THEN** os quatro indicadores mostram zero e não sugerem que houve envio

#### Scenario: Estados mistos do provedor
- **WHEN** notificações persistidas estão `ACCEPTED`, `DELIVERED`, `FAILED`, `PENDING`, `SENDING`, `UNKNOWN`, `NOT_CONFIGURED` ou `SUPPRESSED`
- **THEN** cada notificação é contada uma única vez: `ACCEPTED` em aceitas, `DELIVERED` em entregues, `FAILED` em falhas e os quatro estados restantes em pendentes/indeterminadas; `SUPPRESSED` fica fora das quatro contagens e aceitas não são apresentadas como entregues

#### Scenario: Acesso por outra role
- **WHEN** uma role diferente de Recepcionista solicita a projeção das métricas
- **THEN** o servidor nega a leitura antes de retornar os agregados

#### Scenario: Destinatário protegido
- **WHEN** a projeção das métricas é apresentada na Recepção
- **THEN** somente valores agregados são exibidos e nenhum endereço de e-mail ou corpo de mensagem é exposto
