## Contexto

`AdminAvailabilityState` e `ReceptionAgendaState` já recebem slots reais vindos de PostgreSQL e exibem o horário formatado por `format_clinic_datetime` para o fuso da clínica. O formato persistido e as validações não devem mudar.

## Decisões

1. Adicionar campos `date_label` e `time_label` às projeções de horários com origem na mesma conversão fuso/UTC. Não parsear o locale no browser.
2. Agrupar as projeções em listas pequenas por data ordenada, sem inventar horários ou duração.
3. Criar inputs separados `date` e `time` no Admin, combinando somente durante o submit em ISO local `YYYY-MM-DDTHH:MM` para as validações server-side existentes.
4. Preservar explicitamente o `slot_datetime_local` legado do State para não quebrar integrações existentes, mas priorizar o novo form.
5. Não mudar as transações de `appointment_scheduling/service.py`: operação segura continua revalidando slot disponível no servidor.
6. Estilo baseado em DESIGN.md; use foco visível, grupos semânticos, contexto de paciente e estados vazios claros.
7. Filtros de data existentes continuam definindo o período; agrupamento não finge agenda semanal recorrente.

## Validação

OpenSpec strict, testes de projeção/agrupamento e datas inválidas, Pytest PostgreSQL 16, Reflex compile e QA em navegador com viewport 320/375/768px.
