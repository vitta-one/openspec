# professional-working-hours Specification

## Purpose

Definir o expediente semanal persistido do médico e a publicação de disponibilidade futura, separando regra recorrente de slot individual e protegendo horários já reservados.

## Requirements

### Requirement: Administrador define expediente semanal de profissional ativo
O sistema MUST permitir ao Administrador registrar faixa contínua de dias da semana, início e fim em horário local e duração de slot suportada, sem criar escala para profissional inexistente ou inativo.

#### Scenario: Expediente válido
- **WHEN** o Administrador define dias da semana válidos, início anterior ao fim e duração de 30 ou 60 minutos que divide o intervalo
- **THEN** a regra é validada e persistida para o profissional selecionado

#### Scenario: Dia ou duração inválidos
- **WHEN** intervalo de dias não é contínuo, início não precede o fim ou duração não é suportada
- **THEN** o servidor rejeita a alteração e mantém a regra anterior

#### Scenario: Médico inativo
- **WHEN** o profissional selecionado está desativado
- **THEN** não se publica novo expediente como disponibilidade ativa

### Requirement: Publicação respeita a janela móvel de 45 dias
O sistema MUST publicar slots recorrentes futuros na janela de 45 dias, convertendo horário local para instante consistente e sem fabricar disponibilidade fora da regra.

#### Scenario: Primeira publicação
- **WHEN** uma regra válida é aplicada a um profissional ativo
- **THEN** o sistema gera apenas instantes elegíveis da janela e atribui origem recorrente reconhecível

#### Scenario: Regeneração
- **WHEN** a geração é executada mais de uma vez para a mesma regra e período
- **THEN** os slots já existentes não são duplicados

#### Scenario: Limite e fuso
- **WHEN** o intervalo cruza limites de dia ou o calendário local possui transição de offset
- **THEN** o sistema respeita a configuração de fuso e rejeita instantes locais inválidos em vez de ajustar silenciosamente

### Requirement: Alteração semanal não apaga reservas nem slots manuais
O sistema MUST preservar consultas já reservadas e slots individuais desativados/manuais quando o expediente semanal muda ou é regenerado.

#### Scenario: Reserva existente
- **WHEN** o Administrador modifica uma regra que originou slot já reservado
- **THEN** a consulta e sua reserva permanecem consistentes, sem remarcação automática

#### Scenario: Horário manual
- **WHEN** existe um slot manual ou manualmente desativado dentro da nova janela
- **THEN** a geração não sobrescreve a escolha operacional preexistente

### Requirement: Interface distingue regra persistida e rascunho
A UI de expediente MUST apresentar separadamente a regra salva e os campos editados ainda não confirmados, indicando médico e período selecionados.

#### Scenario: Rascunho não salvo
- **WHEN** o Administrador altera campos sem submeter a edição
- **THEN** o resumo de expediente continua exibindo a regra persistida

#### Scenario: Troca de profissional
- **WHEN** o Administrador seleciona outro médico
- **THEN** o State descarta contexto anterior e carrega somente regra e horários autorizados do novo profissional
