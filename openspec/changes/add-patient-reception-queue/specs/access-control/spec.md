## MODIFIED Requirements

### Requirement: Shell de dashboard por role
O sistema MUST possuir um destino inicial protegido para cada uma das quatro roles. Esses destinos MAY hospedar funcionalidades de negócio definidas por capabilities específicas, desde que cada operação continue submetida à autorização server-side correspondente.

#### Scenario: Administrador conclui login
- **WHEN** um usuário com role Administrador conclui a autenticação
- **THEN** o sistema direciona para o painel administrativo protegido

#### Scenario: Recepcionista conclui login
- **WHEN** um usuário com role Recepcionista conclui a autenticação
- **THEN** o sistema direciona para o painel de recepção protegido

#### Scenario: Médico conclui login
- **WHEN** um usuário com role Médico conclui a autenticação
- **THEN** o sistema direciona para o painel médico protegido

#### Scenario: Financeiro conclui login
- **WHEN** um usuário com role Financeiro conclui a autenticação
- **THEN** o sistema direciona para o painel financeiro protegido
