## ADDED Requirements

### Requirement: Registro clínico para atendimento de fila sem agendamento

A aplicação DEVE oferecer prontuário e prescrição ao Médico responsável também para paciente de pronto atendimento não agendado, sem criar Consulta ou slot fictício, preservando o agendamento funcional existente.

#### Scenario: Paciente chega sem agendar
- **WHEN** a Recepção cadastra/identifica um paciente e o coloca na fila com relato e prioridade informada
- **THEN** existe uma entrada AGUARDANDO persistida
- **AND** nenhum slot é reservado e nenhuma Consulta é agendada

#### Scenario: Médico chama paciente avulso
- **WHEN** um Médico autenticado reivindica a primeira entrada elegível da fila
- **THEN** a entrada inicia o atendimento vinculada a esse Médico
- **AND** um único registro clínico é criado na mesma transação, associado à entrada e não a Consulta agendada

#### Scenario: Médico atende e prescreve
- **WHEN** o Médico responsável preenche e salva o prontuário de uma entrada EM_ATENDIMENTO
- **THEN** os dados são persistidos com autorização vinculada ao atendimento
- **AND** pode criar, revisar e imprimir prescrição associada ao prontuário sem horário agendado artificial

#### Scenario: Revisão e conclusão
- **WHEN** o Médico solicita finalizar o atendimento
- **THEN** a interface solicita revisão explícita da passagem clínica
- **AND** impede a finalização com alterações clínicas ainda não salvas
- **AND** após confirmação a passagem é FINALIZADO e o prontuário fica somente leitura no histórico

#### Scenario: Conteúdo não autorizado
- **WHEN** outro Médico tenta ler ou modificar o prontuário ou prescrição de passagem alheia
- **THEN** o servidor rejeita a operação independentemente da navegação ou do estado client-side

#### Scenario: Consulta agendada continua independente
- **WHEN** a Recepção agenda, reagenda ou confirma a chegada de um paciente agendado
- **THEN** slots, estados de Consulta, médico marcado e histórico mantêm as regras atuais
- **AND** seu registro clínico continua ligado à Consulta, sem duplicar o episódio como prontuário avulso
