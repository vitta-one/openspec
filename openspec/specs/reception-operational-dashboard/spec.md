# reception-operational-dashboard Specification

## Purpose

Definir as projeções operacionais do dashboard da Recepção a partir de registros persistidos, com autorização server-side e sem inferir estado clínico.

## Requirements

### Requirement: Indicadores operacionais usam somente registros persistidos
O sistema MUST computar consultas agendadas hoje não canceladas, entradas aguardando, em atendimento, concluídas hoje, chegadas confirmadas hoje e pendências de chegada, observando o dia no fuso da clínica e sem duplicar eventos.

#### Scenario: Banco vazio
- **WHEN** não existem Consultations nem QueueEntries
- **THEN** os indicadores exibem zero e as próximas consultas exibem estado vazio

#### Scenario: Dia local diferente do UTC
- **WHEN** consultas existem no limite do dia local
- **THEN** os totais usam intervalo convertido corretamente para UTC

### Requirement: Próximas consultas e prioridades não inferem dados
O sistema MUST apresentar até cinco próximas Consultations AGENDADA com data, paciente e profissional, e MUST apresentar contagem de prioridades de entradas AGUARDANDO sem alterar sua ordem nem classificação.

#### Scenario: Consulta cancelada e fila mista
- **WHEN** há consultas canceladas, pacientes em atendimento e prioridade informada pela operação
- **THEN** só os itens elegíveis entram nas projeções correspondentes e nenhuma prioridade é recalculada

### Requirement: Atualização manual e falhas honestas
O sistema MUST disponibilizar atualização manual, horário da leitura bem-sucedida, loading, erro legível e limpar dados sensíveis quando a atualização falhar.

#### Scenario: Erro de leitura
- **WHEN** o banco está indisponível
- **THEN** nenhum número antigo é apresentado como atual e há um aviso

#### Scenario: Atualização da recepcionista
- **WHEN** Recepcionista aciona Atualizar
- **THEN** o servidor revalida a sessão e recalcula agregados
