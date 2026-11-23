## ADDED Requirements

### Requirement: Recepção agenda consulta no modal compartilhado

A Recepção MUST disponibilizar um diálogo único para agendamento a partir da Agenda ou do dashboard. O diálogo MUST permitir escolher um paciente existente autorizado, médico ativo, data e horário reservável, revisar os dados e confirmar utilizando o serviço transacional já existente, sem criar uma rota obrigatória nem uma reserva paralela.

#### Scenario: Agendamento concluído pela Agenda

- **WHEN** a recepcionista abre o modal, seleciona paciente, médico, dia com slot disponível e horário e confirma a revisão
- **THEN** o servidor revalida a reserva, persiste exatamente uma Consulta e a interface fecha o modal, informa sucesso e atualiza a consulta no período correspondente sem realizar check-in

#### Scenario: Agendamento iniciado no dashboard

- **WHEN** a recepcionista aciona Nova consulta no dashboard
- **THEN** o mesmo modal é aberto no dashboard, sem navegação obrigatória para outro formulário

#### Scenario: Profissional sem especialidade vinculada

- **WHEN** o cadastro de um médico ativo não possui especialidade ativa vinculada
- **THEN** a seleção do profissional continua possível sem inventar nem exigir especialidade

#### Scenario: Horário reservado por outra sessão

- **WHEN** o horário é reservado por outra sessão depois de exibido no modal
- **THEN** o servidor rejeita a reserva concorrente sem criar duplicidade e a interface recarrega a disponibilidade, preservando paciente e profissional

#### Scenario: Nenhum horário disponível

- **WHEN** não existem slots futuros disponíveis no intervalo de 45 dias para o profissional
- **THEN** o calendário não oferece dias reserváveis e a interface mostra orientação contextual sem criar horário fictício

#### Scenario: Descarte antes de confirmar

- **WHEN** uma recepcionista fecha o modal com seleção ou busca preenchida
- **THEN** a interface confirma a intenção de descartar, permitindo continuar com os dados existentes

#### Scenario: Consulta salva e falha no refresh

- **WHEN** a persistência confirma a consulta mas a leitura para atualizar Agenda ou dashboard falha
- **THEN** a interface informa que a reserva foi salva e pede atualização, sem sugerir nova confirmação

### Requirement: Recepção utiliza identidade mínima na busca de agendamento

A pesquisa de paciente MUST consultar identidades autorizadas por nome, CPF ou telefone e apresentar somente nome e identificação de contato mascarada. O sistema MUST revalidar o paciente selecionado no servidor antes de confirmar.

#### Scenario: Buscar paciente existente

- **WHEN** a recepcionista digita pelo menos dois caracteres de nome, CPF ou telefone e busca
- **THEN** aparecem somente resultados reais com telefone parcial e nenhum CPF exposto

#### Scenario: Paciente não encontrado

- **WHEN** a pesquisa não encontra pacientes
- **THEN** o diálogo informa ausência de resultados e oferece a rota de cadastro existente, sem duplicar o formulário
