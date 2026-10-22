## ADDED Requirements

### Requirement: Agenda médica pertence ao profissional autenticado
O sistema MUST derivar o profissional por `Professional.user_id == identity.id`, exigir role MEDICO e vínculo ativo e retornar apenas consultas desse profissional.

#### Scenario: Médico sem vínculo
- **WHEN** a conta MEDICO não possui vínculo único e ativo com Professional
- **THEN** a operação falha fechada, limpa dados médicos no cliente e exibe instrução operacional segura

#### Scenario: Médico tenta ampliar escopo por ID
- **WHEN** uma conta MEDICO altera query, rota ou State com professional_id de outra pessoa
- **THEN** a boundary ignora a escolha do cliente e não retorna consultas de outro profissional

### Requirement: Lista de pacientes médicos deriva de consultas
O sistema MUST listar apenas pacientes que possuem Consulta associada ao profissional autenticado. A projeção MUST conter somente identidade e informações operacionais necessárias, sem prontuário ou texto clínico.

#### Scenario: Paciente sem relação assistencial
- **WHEN** não existe consulta do profissional para um paciente
- **THEN** esse paciente não aparece na lista do Médico
