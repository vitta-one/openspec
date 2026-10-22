# Design — fila clínica + consulta agendada

`QueueEntry` é a fonte da verdade do pronto atendimento; `Consultation` e slots continuam sendo a fonte da verdade do agendamento.

Uma `ClinicalCareRecord` pertence **exatamente a um** dos episódios: `consultation_id` ou `queue_entry_id`. Constraint de exclusividade e UNIQUE por origem impedem prontuários ambíguos/duplicados. `Prescription.clinical_care_record_id` permanece obrigatório e autoritativo; seu `consultation_id` torna-se anulável para walk-in.

A chamada da fila mantém seleção por prioridade informada e chegada, `SELECT ... FOR UPDATE SKIP LOCKED` sob a trava do médico. A criação de `ClinicalCareRecord` avulso participa da mesma transação. O atendimento marcado mantém `start_linked_consultation` e disponibilidade reservada.

Todos os serviços clínicos revalidam status `EM_ATENDIMENTO`, paciente e `doctor_user_id`, inclusive prescrições e impressão. Consulta concluída / fila `FINALIZADO` não recebem mutações. O histórico paginado inclui ambas as origens, mas somente depois da finalização. A impressão usa instante real da chamada para walk-in e timestamp programado para Consulta agendada, com nome genérico de campo “Atendimento”.

A revisão de finalização reutiliza `rx.dialog` e tokens Vitta-One. O documento não copia o AgoraVocê. Conserva as rotas e a navegação dos perfis, inclusive `/recepcao/agenda` e `/medico/agenda`.

O modelo de status da fila existente permanece `AGUARDANDO` → `EM_ATENDIMENTO` → `FINALIZADO`, preservando contratos e concorrência atuais. A confirmação de finalização é nova etapa UX; uma separação de status `CHAMADO` fica fora desta migração por exigir redesenho de transições e testes de concorrência.
