## ADDED Requirements

### Requirement: Fluxo de pronto-socorro sem agendamento

O sistema DEVE permitir iniciar um atendimento diretamente a partir da entrada presencial do paciente na fila, sem exigir data ou horário reservado. A Recepção DEVE registrar a prioridade informada, sem inferência automática, e somente o Médico autenticado DEVE chamar e finalizar o atendimento sob sua responsabilidade.

#### Scenario: Recepção registra chegada e prioridade
- **WHEN** a Recepcionista autenticada identifica um paciente válido e informa sintomas e prioridade
- **THEN** o sistema persiste uma entrada na fila com estado AGUARDANDO, horário real de entrada e classificação explicitamente informada
- **AND** não cria uma consulta agendada nem reserva horário

#### Scenario: Médico chama o próximo paciente
- **WHEN** o Médico autenticado está sem atendimento ativo e chama o próximo paciente
- **THEN** o sistema reivindica atomicamente uma entrada AGUARDANDO elegível, ordenada por prioridade e chegada
- **AND** vincula a passagem ao Médico, registrando horário real da chamada
- **AND** a operação não cria um agendamento sintético

#### Scenario: Registro clínico de atendimento presencial
- **WHEN** o Médico responsável acessa seu atendimento EM_ATENDIMENTO originado na fila
- **THEN** pode registrar, salvar e recuperar prontuário e prescrição ligados ao episódio de fila
- **AND** nenhuma conta de outro Médico ou paciente acessa o conteúdo protegido

#### Scenario: Finalização do atendimento
- **WHEN** o Médico responsável finaliza um atendimento sem alterações locais pendentes
- **THEN** a passagem torna-se FINALIZADO, mantendo relatório clínico e prescrições em histórico somente leitura
- **AND** a Recepção não recebe privilégios de escrita sobre esse conteúdo clínico

#### Scenario: Agenda não pertence ao produto
- **WHEN** qualquer perfil acessa a navegação de pronto-socorro
- **THEN** não encontra calendário de reservas, criação de horários, agendamento ou reagendamento
- **AND** não há promessa de consulta futura que não foi realmente marcada

#### Scenario: Dados históricos preexistentes
- **WHEN** existem dados legados de consulta agendada anteriores à mudança de escopo
- **THEN** a migração do pronto-socorro preserva os dados sem apagá-los silenciosamente
- **AND** novas entradas da fila não geram consultas fictícias para manter compatibilidade artificial
