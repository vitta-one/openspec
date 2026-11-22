## ADDED Requirements

### Requirement: Formulário dedicado de cadastro oferece entrada acessível e validação recuperável
O formulário de novo paciente da Recepção MUST manter nome e CPF obrigatórios, telefone opcional, máscara automática de CPF e feedback específico por campo. A UI MUST permitir colar CPF com ou sem pontuação, MUST preservar os valores editados em erro de validação e MUST apresentar o primeiro campo inválido com foco e erro associado programaticamente. A interface MUST usar componentes existentes, ter largura controlada e funcionar por teclado e em telas estreitas.

#### Scenario: Recepcionista digita ou cola CPF sem pontuação
- **WHEN** a Recepcionista preenche CPF válido com 11 dígitos, digitado ou colado
- **THEN** o campo mostra a formatação visual sem exigir pontuação manual, e o servidor valida os mesmos 11 dígitos para persistência

#### Scenario: Dados inválidos são corrigidos no próprio formulário
- **WHEN** a Recepcionista envia nome vazio ou só com espaços, CPF inválido ou telefone inválido preenchido
- **THEN** o servidor rejeita o cadastro, o formulário identifica os campos com erro e mantém os valores para correção sem criar paciente

#### Scenario: Telefone opcional
- **WHEN** a Recepcionista não informa telefone e apresenta nome e CPF válidos
- **THEN** o cadastro pode ser concluído sem telefone

### Requirement: Cadastro de paciente confirma persistência e impede duplicação
A ação de cadastrar paciente MUST validar autorização e entrada no servidor, MUST impedir duas submissões simultâneas pelo State e MUST respeitar a unicidade de CPF no banco, inclusive sob concorrência. Sucesso MUST ser informado somente após persistência confirmada, seguido de navegação à ficha individual do paciente criado. Uma falha posterior de navegação MUST NOT provocar outra inserção automática.

#### Scenario: Cadastro válido encaminha à ficha
- **WHEN** uma Recepcionista autorizada confirma um cadastro válido de CPF ainda inexistente
- **THEN** exatamente um paciente é persistido, sua identificação é preservada e a ficha correspondente é aberta automaticamente

#### Scenario: CPF já cadastrado
- **WHEN** a Recepcionista tenta cadastrar um CPF que já pertence a um paciente
- **THEN** nenhum segundo registro é criado, a tela informa a duplicidade e pode oferecer acesso à ficha existente somente se o servidor autorizar sua consulta

#### Scenario: Cliques repetidos
- **WHEN** a Recepcionista envia o formulário novamente enquanto a operação anterior está em andamento ou após sucesso persistido na mesma tela
- **THEN** o State não emite outra inserção e mantém a identificação do cadastro confirmado

#### Scenario: Persistência confirmada seguida de falha na navegação
- **WHEN** a persistência do cadastro é confirmada, mas o redirecionamento não conclui
- **THEN** o State mantém o ID criado e disponibiliza um caminho para abrir a ficha sem criar novo paciente

#### Scenario: Sessão inválida ou role incompatível
- **WHEN** alguém sem sessão válida ou sem role Recepcionista tenta executar o cadastro diretamente
- **THEN** o servidor nega a operação sem expor dados pessoais ou persistir novos registros
