## ADDED Requirements

### Requirement: Role de Paciente e rotas próprias
O sistema MUST reconhecer `PACIENTE` como role distinta e redirecionar sua sessão validada para `/paciente`. Cada rota protegida MUST revalidar sessão e role no servidor, preservando Admin, Recepção, Médico e Financeiro.

#### Scenario: Login de paciente
- **WHEN** uma conta PACIENTE válida conclui login
- **THEN** o sistema redireciona para `/paciente` e não para área interna

#### Scenario: Paciente tenta rota de equipe
- **WHEN** uma sessão PACIENTE acessa diretamente uma rota de Admin, Recepção, Médico ou Financeiro
- **THEN** o servidor nega o acesso sem retornar dados da outra role

### Requirement: Conta do paciente é vinculada por convite
O sistema MUST vincular uma conta PACIENTE somente após código de ativação válido, convite não expirado/não usado, consentimento registrado e associação controlada pela Recepção/Administração. CPF ou nome nunca são prova de propriedade.

#### Scenario: Convite válido
- **WHEN** o paciente envia e-mail, código e senha válidos pelo formulário de ativação
- **THEN** o servidor cria uma conta PACIENTE, vincula exatamente um cadastro existente, consome o convite e não revela o código em URL, logs ou estado client-side

#### Scenario: Código inválido, expirado ou reutilizado
- **WHEN** o código não é válido para um convite ativo
- **THEN** a resposta é genérica, nenhuma conta é criada e nenhum dado de paciente é retornado

#### Scenario: E-mail já pertence a uma identidade
- **WHEN** o convite tenta criar uma conta com e-mail já usado
- **THEN** nenhuma identidade ou vínculo é sobrescrito e a resposta pública não confirma a existência da conta

### Requirement: Ativação não concede sessão implícita
O sistema MUST exigir login normal depois de ativar a conta, usando o e-mail como identificador canônico e senha escolhida pelo paciente.

#### Scenario: Ativação concluída
- **WHEN** uma ativação é persistida
- **THEN** a página informa sucesso e oferece ir ao login sem colocar segredo na URL
