## ADDED Requirements

### Requirement: Reagendamento mantém trilha de horários
O serviço de reagendamento MUST persistir horário anterior, novo horário, autor e instante na mesma transação que reserva o novo slot e atualiza a consulta.

#### Scenario: Conflito ao reagendar
- **WHEN** o novo slot está indisponível ou qualquer constraint falha
- **THEN** nenhum evento de reagendamento é mantido, o slot anterior e a consulta continuam intactos
