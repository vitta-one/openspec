## Arquitetura
Criar `vitta_one/reception/dashboard/{service,application,state,components}.py`, reaproveitando modelos persistidos. `application` valida sessão/role antes de `service` ler dados. UI usa sidebar atual, states existentes para fila/paciente e agenda. Não duplicar transições.

## Rotas
- `/recepcao`: dashboard de leitura, atualização manual.
- `/recepcao/agenda`: `ReceptionAgendaState`, `reception_agenda_panel` (inclui check-in).
- `/recepcao/pacientes`: `ReceptionQueueState`, identificação e cadastro.
- `/recepcao/fila`: `ReceptionQueueState`, entrada avulsa, reavaliação, retirada e fila.

## Definições
- Agendados hoje: Consultations com `scheduled_at` no dia clínico e status diferente de CANCELADA.
- Aguardando / em atendimento: QueueEntry nos respectivos estados, sem filtro de dia (estoque atual).
- Finalizados hoje: QueueEntry FINALIZADO com `finished_at` no dia clínico, sem somar Consulta.
- Chegadas confirmadas hoje: Consultations CONFIRMADA com `scheduled_at` no dia.
- Pendentes de chegada: Consultations AGENDADA do dia com horário anterior ao instante atual, sem marcar falta ou cancelar.
- Próximas 5: Consultation AGENDADA com horário futuro, ordenada por horário e ID; mostrar somente paciente, médico, horário.
- Prioridades: total por VERMELHO/AMARELO/VERDE apenas dos aguardando.

## Segurança
RBAC aplicado a todos os loaders e queries no servidor. Nenhum campo clínico exposto no dashboard. Estados limpos em falhas, incluindo sessão expirada; sem seeding ou migrations.
