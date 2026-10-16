## ADDED Requirements

### Requirement: Portal de consulta próprio
O portal MUST derivar o paciente exclusivamente da sessão PACIENTE e listar consultas futuras e passadas somente daquele vínculo.

#### Scenario: Paciente consulta a própria agenda
- **WHEN** um paciente autenticado abre um mês/período
- **THEN** vê suas consultas com médico, especialidades disponíveis, data/hora local, status persistido e dados configurados da clínica

#### Scenario: ID de outro paciente
- **WHEN** a sessão altera parâmetros, IDs ou estado para apontar para outra pessoa
- **THEN** a consulta é rejeitada/ignorada e nenhum dado alheio é retornado

#### Scenario: Sem consultas
- **WHEN** o paciente não possui consultas no período
- **THEN** o portal mostra estado vazio verdadeiro e permite navegar para outro período

### Requirement: Reagendamentos preservam histórico visível
O sistema MUST gravar a data anterior e a nova data na mesma transação do reagendamento.

#### Scenario: Consulta reagendada
- **WHEN** a Recepção muda a data de uma consulta
- **THEN** a agenda do paciente mostra a data atual e informa a alteração anterior sem apagar o histórico

### Requirement: Consulta cancelada não desaparece
O sistema MUST exibir o status CANCELADA e a data do compromisso cancelado no histórico do paciente.

#### Scenario: Consulta cancelada
- **WHEN** uma consulta foi cancelada
- **THEN** o paciente pode reconhecê-la como cancelada e não a confunde com compromisso ativo

### Requirement: Endereço verdadeiro da clínica
O sistema MUST exibir nome/endereço somente quando configurados pela implantação.

#### Scenario: Endereço ausente
- **WHEN** configuração de nome/endereço está ausente ou inválida
- **THEN** a UI informa que a Administração ainda precisa configurar o local e não mostra endereço de exemplo

### Requirement: Portal não expõe conteúdo clínico
O portal MUST NOT retornar sintomas, ClinicalCareRecord, histórico clínico, diagnóstico, conduta, Prescription ou itens de Prescrição.

#### Scenario: Paciente abre consulta
- **WHEN** o portal carrega detalhes
- **THEN** apresenta apenas dados operacionais da consulta e clínica
