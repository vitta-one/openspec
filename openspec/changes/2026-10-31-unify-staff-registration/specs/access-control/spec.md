## ADDED Requirements

### Requirement: Cadastro interno unificado de funcionários
O sistema MUST oferecer ao Administrador autenticado uma página de cadastro com nome completo e e-mail obrigatórios e perfil limitado aos tipos de funcionário autorizados. O servidor MUST ignorar dados exclusivos de outros perfis e MUST impedir cadastro por outras roles. Não pode haver cadastro público.

#### Scenario: Cadastro de recepcionista
- **WHEN** Administrador informa nome válido, e-mail não utilizado e senha inicial conforme política existente
- **THEN** uma conta RECEPCIONISTA é persistida com o nome informado e a senha sob hash forte

#### Scenario: Nome ausente ou inválido
- **WHEN** uma tentativa de criação possui nome vazio, só espaços, inferior a 2 ou superior a 160 caracteres
- **THEN** a operação é rejeitada no servidor e nenhuma conta é criada

#### Scenario: Perfil ou sessão inválidos
- **WHEN** usuário sem role ADMINISTRADOR tenta cadastrar funcionário ou submete perfil não autorizado
- **THEN** o servidor nega a operação sem criar identidade ou atribuir privilégios

#### Scenario: Trocar perfil
- **WHEN** Administrador troca o perfil durante o cadastro
- **THEN** nome e e-mail são preservados; os campos específicos mudam sem enviar dados incompatíveis, e eventual perda de dados específicos exige confirmação

#### Scenario: E-mail duplicado ou submissão repetida
- **WHEN** duas tentativas tentam criar identidade com o mesmo e-mail normalizado
- **THEN** no máximo uma conta é persistida e a segunda recebe feedback recuperável

#### Scenario: Primeiro acesso médico sem Resend
- **WHEN** o médico é cadastrado mas o envio de instruções não é configurado ou confirmado
- **THEN** o cadastro é preservado e a interface informa o estado correto, sem alegar envio nem tentar criar a conta novamente

#### Scenario: Erro de entrada ou falha do servidor
- **WHEN** o cadastro falha sem persistir
- **THEN** a página mantém a identificação válida, apresenta erros associados aos campos e permite corrigir e reenviar
