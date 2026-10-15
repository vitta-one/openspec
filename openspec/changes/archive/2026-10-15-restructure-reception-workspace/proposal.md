## Why
Recepção atual mistura agenda, cadastro de pacientes e fila na mesma página. Precisamos de um centro de operação com indicadores reais e tarefas separadas, sem alterar regras clínicas ou dados antigos.

## What Changes
- `/recepcao` passa a ser dashboard com KPIs do dia, fila e próximos agendamentos.
- Novas subrotas protegidas: `/recepcao/agenda`, `/recepcao/pacientes`, `/recepcao/fila`.
- Sidebar com módulos reais e atualização manual do dashboard.
- Queries agregadas server-side com autorização `RECEPCIONISTA`.

## Capabilities
- ADDED: `reception-operational-dashboard`.
- MODIFIED: `access-control`.

## Fora de escopo
Calendário semanal, polling em tempo real, check-in fora da agenda, relatório, auditoria, novos campos de paciente, permissões clínicas, migrações e integrações. Essas melhorias requerem outras changes.
