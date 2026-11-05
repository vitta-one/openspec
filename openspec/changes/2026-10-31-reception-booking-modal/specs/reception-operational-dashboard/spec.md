## ADDED Requirements

### Requirement: Dashboard compartilha a ação de novo agendamento com a Agenda

O dashboard da Recepção MUST abrir o mesmo diálogo de agendamento da Agenda, preservando os indicadores e a visão semanal provenientes de consultas persistidas e atualizando as projeções após nova reserva.

#### Scenario: Nova consulta a partir da operação diária

- **WHEN** a recepcionista seleciona Nova consulta no dashboard
- **THEN** o diálogo de agendamento é aberto localmente e não cria uma segunda lógica de reserva

#### Scenario: Reserva concluída

- **WHEN** a Consulta é persistida pelo fluxo de agendamento
- **THEN** a visão semanal e os indicadores são atualizados usando dados persistidos e filtros existentes, sem duplicar consultas
