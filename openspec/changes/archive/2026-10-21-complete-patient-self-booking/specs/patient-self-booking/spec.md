## ADDED Requirements

### Requirement: Autogendamento vinculado à identidade autenticada

O portal do paciente MUST oferecer seleção de especialidade, médico e horário disponível e confirmar a reserva somente para o Patient vinculado à sessão PACIENTE.

#### Scenario: Da conta ativada à consulta
- **WHEN** a recepção cria um paciente, envia convite com consentimento e o paciente ativa a conta
- **THEN** o paciente pode autenticar e abrir Agendar consulta
- **AND** vê especialidades e profissionais ativos com agenda na clínica

#### Scenario: Reserva válida
- **WHEN** o paciente escolhe uma especialidade ativa, um médico da especialidade e um slot futuro disponível e confirma
- **THEN** o servidor persiste um único Consultation do paciente autenticado
- **AND** marca o slot como reservado e a consulta aparece na agenda do paciente, médico e recepção

#### Scenario: Proteção de identidade
- **WHEN** o navegador informa profissional, especialidade, ou slot forjados, ou tenta chamar operação sem sessão PACIENTE
- **THEN** o servidor rejeita antes de persistir qualquer consulta

#### Scenario: Conflito e concorrência
- **WHEN** duas operações tentam reservar o mesmo slot ou o paciente já possui consulta no horário
- **THEN** somente a operação elegível confirma a reserva
- **AND** as demais recebem mensagem para escolher horário diferente sem apagar a reserva existente

#### Scenario: Recepção preserva contexto
- **WHEN** uma recepcionista cadastra ou seleciona paciente e decide agendar
- **THEN** a agenda abre com esse paciente selecionado sem nova busca de CPF

#### Scenario: Atendimento continua
- **WHEN** a recepção confirma chegada de consulta agendada e médico chama pela fila
- **THEN** a consulta mantém seu vínculo a médico, paciente e registro clínico
- **AND** prontossocorro avulso continua disponível como fluxo separado
