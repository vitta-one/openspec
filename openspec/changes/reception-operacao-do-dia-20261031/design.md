# Decisão técnica — operação diária

## Implementação
A página `/recepcao` continua usando `reception_dashboard()` e `ReceptionDashboardState.load` no fluxo protegido existente.

O dashboard monta os componentes já disponíveis `_appointments_table`, `_reception_day_toolbar`, `_appointment_details_dialog` e `reception_agenda_dialogs`. A busca e o filtro preservam a paginação SQL e as restrições da aplicação de Recepção.

Ação primária `Nova consulta`: `/recepcao/agenda/nova`. Ações de paciente/fila navegam às rotas atuais. Check-in, reagendamento e cancelamento usam o `ReceptionAgendaState` e serviços já validados no servidor.

Os cinco KPIs continuam **globais**: consulta do dia em horário local (exceto canceladas), fila e atendimento em tempo corrente, chegadas pendentes por consulta agendada vencida e concluídos pela data de conclusão. O filtro por profissional não modifica os KPIs, e a UI esclarece essa distinção.

## Estados
- Antes da primeira leitura: carregamento explícito.
- Falha: erro visível; dados de pacientes descartados pelo State.
- Nenhum registro: estado vazio sem sugerir que não existem outras tarefas.
- Filtro sem correspondência: instrução para limpar filtro.
- Zero ou uma página: sem controles de paginação.
- Refresh: preserva busca/filtro e bloqueia clique simultâneo; o evento periódico mantém guarda própria.

## Segurança
`reception_day_operations` e `reception_overview` exigem sessão válida e `Role.RECEPCIONISTA` antes de ler registros; mutações permanecem na Agenda, sem nova autorização na UI como substituta do servidor.

## Verificações
Pytest de projeção/RBAC e regressão de composição; OpenSpec strict; compilação Reflex; QA navegador em 320, 390, 768, 1024 e 1440 px, teclado, menus e modais. Sem migração de banco.
