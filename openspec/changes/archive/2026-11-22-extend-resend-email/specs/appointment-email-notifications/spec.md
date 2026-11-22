# Spec Delta — Comunicação de agenda

## Purpose

Notificar pacientes elegíveis sobre eventos reais da agenda, com gatilhos explícitos, frequência limitada, horário local consistente e lembretes sem duplicação.

## ADDED Requirements

### Requirement: Confirmação de reserva após commit
O sistema MUST solicitar uma confirmação após criação bem-sucedida de Consulta AGENDADA, para paciente com autorização de agenda ativa e e-mail de conta vinculada válido. MUST NOT confundir confirmação de reserva com check-in CONFIRMADA nem enviar novamente por check-in. Rollback MUST NOT gerar notificação.

#### Scenario: Reserva por Recepção ou portal
- **GIVEN** destinatário elegível
- **WHEN** reserva autorizada é persistida por qualquer fluxo existente
- **THEN** registra uma intenção por Consulta/revisão inicial, com data e hora locais, sem diagnóstico ou motivo clínico.

#### Scenario: Consulta confirmada na chegada
- **GIVEN** confirmação da reserva já foi solicitada
- **WHEN** Recepção efetua check-in e Consulta passa a CONFIRMADA
- **THEN** não gera segunda confirmação de reserva.

#### Scenario: Falha ou destinatário inelegível
- **WHEN** reserva perde concorrência, transação falha ou não há autorização/endereço válido
- **THEN** não envia e-mail de confirmação; operação clínica preserva seu próprio resultado.

### Requirement: Reagendamento e cancelamento comunicam transição real
O sistema MUST solicitar no máximo uma mensagem para cada reagendamento ou cancelamento efetivamente persistido e autorizado. Reagendamento MUST identificar data/hora anteriores e novas; cancelamento MUST identificar o compromisso cancelado. Destinatário e preferência MUST ser revalidados no envio. Evento repetido ou ação negada MUST NOT comunicar transição inexistente.

#### Scenario: Reagendamento persistido
- **WHEN** Consulta AGENDADA é movida para horário disponível com histórico salvo
- **THEN** uma intenção usa a identidade da alteração, informa horários corretos e invalida lembrete ainda pendente da revisão antiga.

#### Scenario: Cancelamento persistido
- **WHEN** cancelamento permitido é confirmado no banco
- **THEN** solicita mensagem única e suprime lembretes pendentes, sem cancelar cobrança financeira automaticamente.

#### Scenario: Corrida ou operação negada
- **WHEN** novo horário fica ocupado ou o estado não permite cancelamento
- **THEN** preserva o compromisso anterior e não solicita comunicação de sucesso.

### Requirement: Lembrete único de 24 horas
O sistema MUST avaliar lembretes a cada 5 minutos e enviar uma única mensagem por revisão do horário entre 24h e 23h antes da Consulta, somente para AGENDADA/CONFIRMADA futura e destinatário elegível. MUST revalidar situação e horário no processamento. Fora dessa janela, MUST suprimir lembrete atrasado, sem compensação automática.

#### Scenario: Antecedência correta
- **GIVEN** Consulta daqui a 23h55, autorização ativa e nenhum lembrete dessa revisão
- **WHEN** o processamento periódico ocorre
- **THEN** solicita uma mensagem e execuções seguintes não repetem o lembrete.

#### Scenario: Reagendamento ou cancelamento antes do envio
- **WHEN** intenção de lembrete antiga é processada após mudar horário ou cancelar
- **THEN** suprime a intenção antiga; nova revisão só é elegível dentro da própria janela.

#### Scenario: Job atrasado e execução simultânea
- **WHEN** consumidor retorna faltando menos de 23h ou dois consumidores competem
- **THEN** respectivamente suprime o lembrete atrasado ou permite somente uma solicitação de envio.

### Requirement: Comunicação não determina sucesso clínico
Falha, ausência de configuração ou resultado desconhecido no envio MUST NOT desfazer agendamento, reagendamento, cancelamento ou check-in. A interface MUST informar separadamente resultado da operação e situação da comunicação, sem alegar entrega sem evidência.

#### Scenario: Resend indisponível
- **WHEN** a consulta foi persistida e o envio falha
- **THEN** a Consulta permanece válida e o registro de comunicação informa seu próprio estado.
