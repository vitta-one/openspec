## MODIFIED Requirements

### Requirement: Cadastro mínimo de paciente pela Recepção
O sistema MUST permitir que um usuário com role Recepcionista cadastre um paciente com nome e CPF válidos e telefone brasileiro opcional com DDD. O CPF MUST ser normalizado para persistência e MUST permanecer único. Um telefone preenchido MUST ser normalizado para dígitos e conter 10 ou 11 dígitos.

#### Scenario: Novo paciente válido
- **WHEN** uma Recepcionista autenticada informa nome e CPF válidos ainda não cadastrados, com ou sem telefone válido
- **THEN** o sistema cria exatamente um paciente e disponibiliza esse paciente para entrada na fila

#### Scenario: CPF inválido
- **WHEN** a Recepcionista informa um CPF que não possui formato e dígitos verificadores válidos
- **THEN** o sistema rejeita o cadastro sem persistir o paciente e apresenta erro associado ao campo

#### Scenario: CPF já cadastrado
- **WHEN** a Recepcionista tenta cadastrar um CPF já existente
- **THEN** o sistema não cria paciente duplicado e informa que o cadastro existente deve ser utilizado

#### Scenario: Telefone ausente ou inválido
- **WHEN** a Recepcionista deixa o telefone vazio ou informa um telefone preenchido com comprimento diferente de 10 ou 11 dígitos
- **THEN** o telefone ausente é aceito e o telefone inválido é rejeitado sem persistir o paciente

## ADDED Requirements

### Requirement: Busca rápida de pacientes pela Recepção
O sistema MUST permitir que uma Recepcionista autenticada localize cadastros por nome, telefone ou CPF e MUST retornar somente identificador, nome e telefone. A busca MUST exigir role Recepcionista, ter limite de resultados e MUST NOT expor prontuário ou conteúdo clínico.

#### Scenario: Paciente encontrado
- **WHEN** a Recepcionista busca um paciente persistido por nome, telefone ou CPF
- **THEN** o sistema retorna somente os campos mínimos de identidade e permite selecionar o cadastro existente

#### Scenario: Acesso incompatível
- **WHEN** uma pessoa sem role Recepcionista solicita a busca
- **THEN** o servidor nega o acesso antes de retornar dados do paciente
