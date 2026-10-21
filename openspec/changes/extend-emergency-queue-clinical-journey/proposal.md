# Change: completar a jornada clínica da fila sem perder agendamentos

## Problema
O Vitta-One já recebe pacientes de pronto-socorro sem agendamento, mas o prontuário e a prescrição só funcionam para Consultas agendadas. O AgoraVocê fornece a referência **de jornada**, não de estética, componentes ou código.

## Objetivo
Permitir a mesma sequência funcional do atendimento presencial: recepção identifica/cadastra → prioriza e insere na fila → médico chama e identifica paciente → registra história/conduta → prescreve → revisa → finaliza → consulta histórico.

## Escopo
- Prontuário e prescrição também para passagem sem agendamento.
- Vínculo seguro ao `QueueEntry`, com constraints, transação e autorização por médico.
- Histórico e impressão por data real de atendimento, inclusive para passagem sem agenda.
- Revisão explícita antes de finalizar; impedir perda de edição.
- Manter integralmente agenda, slots, reserva, reagendamento, check-in e consulta agendada.
- Conservar design Vitta-One, rotas, tipografia, estrutura e perfis. Não reutilizar telas/estilos do AgoraVocê.

## Segurança
Não criar consulta artificial, não apagar agendamentos ou prontuários legados, não expor PHI de outros pacientes/médicos. Migração é aditiva e downgrade recusa apagar episódios clínicos sem planejamento.
