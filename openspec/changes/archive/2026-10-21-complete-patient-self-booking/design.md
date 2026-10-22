# Decisões

- A aplicação `patient_schedule_own_consultation` não recebe `patient_id`, apenas dados de seleção de especialidade, médico e slot; resolve o Patient pela identidade da sessão e delega ao `schedule_consultation`.
- Descoberta separada em `patient_portal.booking`: especialidades ativas com profissional ativo, profissionais da especialidade, slots disponíveis no intervalo de 45 dias. Não retorna pacientes ou consultas alheias.
- O servidor revalida `ProfessionalSpecialty`, médico ativo e especialidade ativa. A operação de agenda obtém lock e verifica disponibilidade; recusas de conflito não deixam reserva parcial.
- `PatientBookingState` tem estado transitório de seleção e confirmação; limpar a seleção ao alterar especialidade/médico. Não usar ID client-side como autorização.
- A recepção preserva o paciente selecionado ao entrar na agenda; não requer pesquisar CPF novamente.
- O agendamento visível para o médico e a recepção é o mesmo `Consultation`, sem tabela adicional.
- Fluxos de pronto-socorro e consultas agendadas permanecem separados no ingresso e convergem ao atendimento.
