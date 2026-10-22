# Portal do paciente — data antes de horário

A reserva pelo paciente continua usando a mesma agenda transacional
da Recepção, com disponibilidade criada a partir do expediente semanal do médico.

1. O Administrador configura em **Administração → Expediente semanal do médico**
   os dias (segunda a domingo), horas inicial/final e duração por consulta (30/60 min).
2. Em **/paciente/agendar**, o paciente escolhe especialidade e médico.
3. **3. Escolha o dia:** um seletor exibe apenas datas que possuem slots livres
   para esse médico, nos próximos 45 dias. Não são apresentados horários nesta etapa.
4. **4. Escolha o horário:** somente após a data ser selecionada, são mostradas
   as horas livres daquela data, em botões compactos responsivos.
5. Ao clicar em um horário, o paciente revisa médico, dia e hora, confirmando
   a reserva. A confirmação é revalidada no servidor; um slot ocupado ou
   removido será recusado mesmo com o formulário antigo aberto.

Alterar médico ou especialidade limpa o dia escolhido. Em caso de conflito,
a disponibilidade é recarregada e datas que ficaram sem horário são desmarcadas.
Preserva-se o limite de 45 dias e o histórico de consultas.

**Nota:** esta alteração foi solicitada para integração direta sem execução do CI.
Os testes de Chromium foram atualizados para o seletor, mas não executados.
