## ADDED Requirements

### Requirement: Edição cadastral isolada na ficha de paciente
A Recepção MUST disponibilizar uma ação específica de edição cadastral, separada do convite de acesso e do agendamento. A interface MUST manter um rascunho independente até a persistência, atualizar nome e telefone autorizados e preservar CPF e vínculo com conta.

#### Scenario: Atualização válida
- **WHEN** a recepcionista autorizada altera o nome ou telefone e confirma o salvamento
- **THEN** o servidor valida a sessão, o paciente e os campos, persiste os valores e a ficha exibe os dados atualizados

#### Scenario: Formulário inválido
- **WHEN** nome é vazio/composto por espaços ou telefone informado é inválido
- **THEN** o servidor rejeita a alteração, a interface mantém os valores digitados e apresenta mensagem de erro contextual

#### Scenario: Cancelamento
- **WHEN** a recepcionista fecha o modal antes de salvar
- **THEN** o cadastro persistido permanece inalterado e a ficha não exibe valores provisórios

#### Scenario: Estado ou identidade adulterados
- **WHEN** a sessão perde a autorização ou o identificador de paciente não corresponde à ficha aberta
- **THEN** nenhuma alteração é persistida e a operação é rejeitada
