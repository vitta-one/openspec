# staff-management Specification

## Purpose

Definir a administração operacional de funcionários do Vitta One, distinta da autenticação e do cadastro clínico de profissionais, usando apenas identidades e vínculos persistidos e autorizados.

## Requirements

### Requirement: Administrador cria funcionários por fluxos suportados
O sistema MUST restringir o cadastro interno ao Administrador autenticado e MUST encaminhar cada perfil para o serviço de identidade e vínculo adequado, sem criar permissões ou perfis não suportados.

#### Scenario: Recepcionista válida
- **WHEN** o Administrador informa nome, e-mail normalizado e credencial válida para Recepcionista
- **THEN** o servidor persiste uma identidade RECEPCIONISTA única com hash da senha, sem expor credencial no diretório

#### Scenario: Médico válido
- **WHEN** o Administrador inicia cadastro Médico e informa dados válidos com especialidades opcionais
- **THEN** o fluxo reutiliza a criação transacional de identidade MEDICO e vínculo Professional descrita em professional-specialty-management

#### Scenario: Perfil não permitido
- **WHEN** um formulário modificado tenta cadastrar role não suportada no fluxo interno
- **THEN** a operação é rejeitada sem persistir conta

#### Scenario: Duplicidade
- **WHEN** já existe conta com o e-mail normalizado
- **THEN** o sistema rejeita a nova identidade sem redefinir senha de terceiros

### Requirement: Diretório de funcionários deriva de contas autorizadas
O sistema MUST mostrar apenas contas internas elegíveis com nome real quando existente, e-mail, perfil e estado operacional explicitamente suportado; MUST NOT inferir funcionário desativado quando esse estado não existe no modelo.

#### Scenario: Nome ausente
- **WHEN** identidade legada não possui display_name
- **THEN** a interface apresenta identificação neutra, e-mail distinto e não inventa um nome

#### Scenario: Busca e filtros
- **WHEN** o Administrador combina nome/e-mail, role e filtros disponíveis
- **THEN** a listagem considera somente registros autorizados, apresenta contagem e paginação coerentes

#### Scenario: Diretório vazio
- **WHEN** não existem funcionários elegíveis ou a busca não corresponde a registros
- **THEN** a interface apresenta o vazio correto, sem números fictícios

### Requirement: Ficha individual de funcionário limita dados e ações
O sistema MUST carregar a ficha por identificador apenas após revalidar role e registro e MUST apresentar somente dados de identidade e vínculo permitidos.

#### Scenario: Ficha válida
- **WHEN** o Administrador abre a ficha de RECEPCIONISTA ou MEDICO existente
- **THEN** vê dados administrativos persistidos e associação profissional/especialidades quando aplicável

#### Scenario: Funcionário inexistente
- **WHEN** o ID não existe ou não pertence a tipo de funcionário permitido
- **THEN** o servidor retorna estado neutro sem expor conta alheia

#### Scenario: Ação não implementada
- **WHEN** a interface não possui serviço real de edição, bloqueio ou desligamento de usuário
- **THEN** a ficha não apresenta botão que simule essas ações

### Requirement: Autorizações de funcionários são server-side
Toda consulta e mutação de funcionários MUST revalidar a sessão, a role Administrador e os identificadores envolvidos, sem considerar proteção visual suficiente.

#### Scenario: Recepção tenta listar equipe
- **WHEN** Recepcionista ou Médico invoca diretamente o State ou serviço do diretório
- **THEN** o servidor nega a operação sem retornar dados

#### Scenario: Sessão expirada
- **WHEN** o Administrador perde a sessão antes da operação
- **THEN** o servidor rejeita a leitura ou gravação e a interface limpa dados protegidos
