## ADDED Requirements

### Requirement: Edição e alternância de especialidades rejeitam estado obsoleto
O sistema MUST ler no servidor o registro de especialidade antes de abrir sua edição e MUST rejeitar edições e alterações de situação baseadas em um estado anterior ao persistido por outra transação, sem apagar o registro nem suas associações históricas.

#### Scenario: Edição iniciada a partir de listagem desatualizada
- **WHEN** o Administrador abre a edição de uma especialidade exibida no diretório
- **THEN** o formulário carrega o nome atual persistido no banco após autorização

#### Scenario: Outro usuário já renomeou a especialidade
- **WHEN** o Administrador tenta salvar a alteração com o nome original que já não corresponde ao registro persistido
- **THEN** o servidor rejeita a gravação, preserva o conteúdo digitado e informa que é necessário reabrir a edição

#### Scenario: A situação foi alterada por outra sessão
- **WHEN** o Administrador tenta desativar ou reativar a especialidade a partir de uma situação desatualizada
- **THEN** o servidor rejeita a operação sem reverter a alteração concorrente

### Requirement: Erros de especialidade aparecem no formulário e sucesso não ocupa a página
O sistema MUST apresentar erro de validação ou persistência junto ao campo do modal, preservando o valor e mantendo o diálogo aberto; MUST enviar confirmação compacta apenas após uma mutação persistida e atualizar a listagem de acordo com filtros vigentes.

#### Scenario: Cadastro inválido ou duplicado
- **WHEN** o servidor rejeita um cadastro de especialidade
- **THEN** o valor digitado permanece no modal, com mensagem associada ao campo, e não há sucesso

#### Scenario: Operação bem-sucedida
- **WHEN** cadastro, edição ou mudança de situação é confirmada no banco
- **THEN** a listagem é atualizada sem recarregar a página e um toast de sucesso é emitido
