## MODIFIED Requirements

### Requirement: Roles fixas do domínio
O sistema MUST reconhecer exatamente as roles Administrador, Recepcionista, Médico, Paciente e Financeiro para controle de acesso nesta capability.

#### Scenario: Usuário autenticado possui uma role válida
- **WHEN** a sessão de um usuário autenticado é carregada
- **THEN** o sistema associa o usuário a uma das cinco roles previstas e usa essa role nas decisões de autorização

### Requirement: Shell de dashboard por role
O sistema MUST possuir um destino inicial protegido para cada uma das cinco roles. Esses destinos MAY hospedar funcionalidades de negócio definidas por capabilities específicas, desde que cada operação continue submetida à autorização server-side correspondente.

#### Scenario: Administrador conclui login
- **WHEN** um usuário com role Administrador conclui a autenticação
- **THEN** o sistema direciona para o painel administrativo protegido

#### Scenario: Recepcionista conclui login
- **WHEN** um usuário com role Recepcionista conclui a autenticação
- **THEN** o sistema direciona para o painel de recepção protegido

#### Scenario: Médico conclui login
- **WHEN** um usuário com role Médico conclui a autenticação
- **THEN** o sistema direciona para o painel médico protegido

#### Scenario: Paciente conclui login
- **WHEN** um usuário com role Paciente conclui a autenticação
- **THEN** o sistema direciona para o portal protegido vinculado ao próprio cadastro clínico

#### Scenario: Financeiro conclui login
- **WHEN** um usuário com role Financeiro conclui a autenticação
- **THEN** o sistema direciona para o painel financeiro protegido

## ADDED Requirements

### Requirement: Novos recursos exigem autorização por vínculo
O sistema MUST combinar sessão, role e vínculo do recurso em cada leitura ou mutação de exame, assinatura, conta, cobrança e pagamento; identificadores fornecidos pelo cliente MUST NOT ampliar o escopo autorizado.

#### Scenario: Médico solicita documento de atendimento próprio
- **WHEN** o vínculo profissional e clínico é válido
- **THEN** o servidor permite somente as ações previstas para o estado do recurso

#### Scenario: Identificador válido fora do escopo
- **WHEN** uma identidade autenticada usa id existente pertencente a outro Paciente ou profissional
- **THEN** o servidor nega a operação sem retornar conteúdo protegido

