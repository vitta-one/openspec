## ADDED Requirements

### Requirement: Ficha operacional autorizada do paciente

A Recepção SHALL consultar na ficha individual somente identidade e registros operacionais de um paciente persistido, incluindo CPF mascarado, telefone opcional, consultas futuras e anteriores, entrada ativa e movimentações encerradas na fila. O servidor SHALL revalidar a sessão e a role antes de cada leitura e não SHALL retornar sintomas, diagnósticos, prescrições ou outras informações clínicas dessa projeção.

#### Scenario: Recepcionista abre paciente existente

- **WHEN** uma recepcionista autenticada abre a ficha de um paciente persistido
- **THEN** o sistema mostra identificação mascarada, próximas consultas, situação da fila e histórico limitado aos registros desse paciente
- **AND** não envia CPF completo nem campos clínicos à interface

#### Scenario: Paciente inexistente ou acesso indevido

- **WHEN** o ID da rota é inválido, o paciente não existe ou a sessão não está autorizada
- **THEN** o sistema não revela dados pessoais
- **AND** apresenta um estado não encontrado ou redireciona para autenticação/acesso negado conforme o caso

#### Scenario: Histórico grande ou ausência de dados

- **WHEN** o paciente possui mais de seis consultas anteriores
- **THEN** a Recepção pode navegar pelas páginas do histórico ordenadas por data
- **AND** um paciente sem registros recebe mensagens vazias específicas por seção

### Requirement: Identificação da entrada ativa da fila

A ficha SHALL distinguir entradas ativas de entradas encerradas, sem alterar prioridade ou ordenação clínica.

#### Scenario: Paciente com entrada ativa

- **WHEN** o paciente possui entrada AGUARDANDO ou EM_ATENDIMENTO
- **THEN** a ficha mostra situação, prioridade e horário de entrada
- **AND** oferece acesso à fila sem exibir ação para adicionar uma nova entrada

#### Scenario: Entrada avulsa duplicada

- **WHEN** duas operações tentam adicionar o mesmo paciente com entrada ativa à fila avulsa
- **THEN** o serviço impede a duplicação sob serialização transacional no PostgreSQL
- **AND** não altera a prioridade da entrada existente

#### Scenario: Check-in agendado com fila ativa

- **WHEN** uma consulta agendada tenta confirmar chegada enquanto o mesmo paciente possui entrada ativa na fila
- **THEN** o serviço recusa criar outra entrada, preservando o estado da consulta e a prioridade existente
- **AND** uma nova confirmação poderá ser realizada após encerramento legítimo da entrada anterior

#### Scenario: Paciente com somente entradas encerradas

- **WHEN** um paciente possui apenas entradas FINALIZADO ou RETIRADO
- **THEN** a ficha mostra que não existe entrada ativa
- **AND** permite iniciar o fluxo de nova entrada com as validações de domínio existentes
