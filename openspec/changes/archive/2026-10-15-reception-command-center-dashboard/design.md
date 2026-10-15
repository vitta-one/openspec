## Contexto e auditoria

Inventário rastreável em `docs/qa/reception-workspace-audit-2026-10-15.md`. A change `restructure-reception-workspace` foi consolidada/arquivada na mesma branch com tarefas marcadas a partir do PR #309, seus testes e CI.

## Fonte dos dados

- Consultas hoje: `Consultation.scheduled_at` no intervalo do dia clínico convertido para UTC, status diferente de `CANCELADA`.
- Chegadas confirmadas: `Consultation.status == CONFIRMADA` no mesmo intervalo.
- Pendências: `Consultation.status == AGENDADA`, dentro do dia clínico e `scheduled_at < as_of`; quantidade total e no máximo cinco registros mais antigos. Pendência não é falta, urgência nem cancelamento.
- Aguardando / em atendimento: estoque atual de `QueueEntry` nos estados existentes, sem limite de data.
- Finalizados hoje: `QueueEntry.status == FINALIZADO` e `finished_at` no intervalo do dia clínico.
- Prioridades: somente entradas `AGUARDANDO`, usando os valores já atribuídos.

Duas consultas agregadas retornam contagens de consultas e fila. Duas consultas com joins leem, respectivamente, as cinco próximas consultas futuras e as cinco pendências mais antigas. Não há leitura de sintomas ou conteúdo clínico.

## Arquitetura e UI

- Manter `application.reception_overview` como fronteira `RECEPCIONISTA` e reaproveitar `ReceptionDashboardState`.
- Estender o snapshot tipado com a lista das pendências.
- O primeiro carregamento mantém estado visual de carregamento; zeros só aparecem após sucesso. Durante refresh, a última leitura bem-sucedida permanece explicitamente identificada. Uma falha limpa o snapshot e oferece nova tentativa.
- Cabeçalho: botão primário para agendar, atalho de cadastro e refresh manual. Não exibir estado de conexão, pois o app não tem sinal independente verificável.
- KPIs em grade responsiva; próximas consultas com paciente, profissional, data/hora, situação `Agendada` e navegação para a Agenda.
- “Precisa da sua atenção” mostra até cinco itens, o total e ação para revisão na Agenda. Confirmação de chegada continua dentro do fluxo existente da Agenda.
- Usar superfícies, tipografia, cores e componentes do design system existente; nenhum token global ou modelo muda.

## Segurança e riscos

O loader continua revalidando sessão e role no servidor. O link de ação abre a rota canônica existente; não promete filtrar ou selecionar um registro quando a Agenda não oferece esse parâmetro. Nomes de paciente e profissional já são usados na lista atual e permanecem restritos à role de Recepção. O limite da lista não altera a contagem total. Falhas não deixam métricas antigas apresentadas como atuais.
