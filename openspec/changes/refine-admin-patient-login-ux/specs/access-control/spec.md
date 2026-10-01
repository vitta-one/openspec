## MODIFIED Requirements

### Requirement: Login local com credenciais válidas
O sistema MUST permitir que um usuário previamente cadastrado se autentique utilizando e-mail e senha válidos, MUST criar uma sessão autenticada associada à identidade e à role desse usuário e MUST apresentar o formulário de autenticação de forma utilizável em desktop, tablet, mobile e viewports de baixa altura.

#### Scenario: Credenciais válidas
- **WHEN** um usuário informa um e-mail cadastrado e a senha correspondente
- **THEN** o sistema autentica o usuário, cria a sessão e direciona para o shell de dashboard compatível com sua role

#### Scenario: Credenciais inválidas
- **WHEN** um usuário informa e-mail inexistente ou senha incorreta
- **THEN** o sistema não cria sessão autenticada e apresenta uma mensagem genérica de falha que não revela qual credencial está incorreta

#### Scenario: Login em viewport estreita ou baixa
- **WHEN** a tela de login é aberta em viewport que não comporta confortavelmente o layout dividido
- **THEN** o formulário permanece integralmente legível e alcançável, sem clipping de campos ou ação de entrada, e o conteúdo visual secundário é reduzido ou removido

### Requirement: Senha permanece mascarada com controle acessível de revelação
O campo de senha MUST iniciar mascarado e MUST permitir revelar ou ocultar o valor por um controle de ícone centralizado dentro da área do campo, sem alterar o valor digitado.

#### Scenario: Revelar senha
- **WHEN** o usuário aciona o controle de revelar senha
- **THEN** o valor permanece inalterado, o campo passa a exibi-lo e o controle comunica estado e nome acessível equivalentes a “Ocultar senha”

#### Scenario: Ocultar senha
- **WHEN** o usuário aciona novamente o controle
- **THEN** o campo volta a mascarar o valor e o controle comunica estado e nome acessível equivalentes a “Mostrar senha”
