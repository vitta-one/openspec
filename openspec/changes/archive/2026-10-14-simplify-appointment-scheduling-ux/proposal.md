## Why

O QA do Vitta-One revelou que a escala de horários exige familiaridade com "slots" e apresenta uma lista corrida que mistura dias/profissionais e data/hora em um único input.

## What Changes

- Agrupar horários por dia no Administrador e na Recepção, com data legível, hora destacada e profissional identificado.
- Separar data e hora ao adicionar disponibilidade, mantendo armazenamento UTC e fuso da clínica.
- Simplificar descrições, filtros, estados vazios e ações.
- Reutilizar serviços protegidos e mecanismos existentes de agendamento, reagendamento e cancelamento.

## Modified Capabilities
- `appointment-scheduling`.

## Out of Scope
- Recorrência, duração automática de consulta, intervalos clínicos, alteração no lifecycle.
- Modelos, migrações, integrações externas.
- Exclusão de horários existentes ou alteração de RBAC.
