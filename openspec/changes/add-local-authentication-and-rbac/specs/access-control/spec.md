## Purpose

Fornecer autenticação local e controle de acesso baseado em roles para identificar o usuário atual e proteger páginas, dados e ações do Vitta-One antes da implementação dos módulos de negócio.

## ADDED Requirements

### Requirement: Login local com credenciais válidas
O sistema DEVE permitir que um usuário previamente cadastrado se autentique utilizando e-mail e senha válidos e DEVE criar uma sessão autenticada associada à identidade e à role desse usuário.

#### Scenario: Credenciais válidas
- **WHEN** um usuário informa um e-mail cadastrado e a senha correspondente
- **THEN** o sistema autentica o usuário, cria a sessão e direciona para o shell de dashboard compatível com sua role

#### Scenario: Credenciais inválidas
- **WHEN** um usuário informa e-mail inexistente ou senha incorreta
- **THEN** o sistema não cria sessão autenticada e apresenta uma mensagem genérica de falha que não revela qual credencial está incorreta

### Requirement: Senhas não podem ser armazenadas em texto puro
O sistema DEVE persistir somente uma representação criptograficamente segura da senha e DEVE verificar a senha informada contra essa representação no lado servidor.

#### Scenario: Persistência de credencial
- **WHEN** uma credencial de usuário é criada ou alterada
- **THEN** nenhuma senha em texto puro é persistida no banco de dados, logs ou arquivos versionados

### Requirement: Sessão autenticada
O sistema DEVE manter uma sessão autenticada suficiente para identificar o usuário e sua role durante a navegação e DEVE revalidar a sessão no lado servidor antes de liberar dados ou ações protegidas.

#### Scenario: Recarregamento de página
- **WHEN** um usuário com sessão válida recarrega uma página protegida
- **THEN** o sistema restaura o contexto autenticado sem exigir novo login enquanto a sessão permanecer válida

#### Scenario: Sessão ausente ou inválida
- **WHEN** uma página, carregamento de dados ou ação protegida é solicitada sem uma sessão válida
- **THEN** o sistema nega o acesso e direciona o fluxo de interface para autenticação sem expor dados privados

### Requirement: Logout invalida a sessão
O sistema DEVE permitir que um usuário autenticado encerre sua sessão e DEVE impedir reutilização dessa sessão após o logout.

#### Scenario: Logout concluído
- **WHEN** um usuário autenticado executa logout
- **THEN** o sistema invalida a sessão atual, limpa o contexto autenticado e direciona para a página de login

### Requirement: Roles fixas do domínio
O sistema DEVE reconhecer exatamente as roles Administrador, Recepcionista, Médico e Financeiro para controle de acesso nesta capability.

#### Scenario: Usuário autenticado possui uma role válida
- **WHEN** a sessão de um usuário autenticado é carregada
- **THEN** o sistema associa o usuário a uma das quatro roles previstas e usa essa role nas decisões de autorização

### Requirement: Autorização deve ser aplicada no servidor
O sistema DEVE validar identidade e role no lado servidor em todo event handler, loader, computed var ou operação que leia ou modifique dados protegidos. Ocultar componentes ou redirecionar páginas no frontend NÃO DEVE ser considerado controle de acesso suficiente.

#### Scenario: Tentativa de ação sem permissão
- **WHEN** um usuário autenticado tenta acionar diretamente uma operação não permitida para sua role
- **THEN** o servidor rejeita a operação e nenhum dado protegido é criado, alterado, removido ou retornado indevidamente

### Requirement: Shell de dashboard por role
O sistema DEVE possuir um destino inicial protegido para cada uma das quatro roles, ainda sem implementar os módulos finais de negócio.

#### Scenario: Administrador conclui login
- **WHEN** um usuário com role Administrador conclui a autenticação
- **THEN** o sistema direciona para o shell do painel administrativo

#### Scenario: Recepcionista conclui login
- **WHEN** um usuário com role Recepcionista conclui a autenticação
- **THEN** o sistema direciona para o shell do painel de recepção

#### Scenario: Médico conclui login
- **WHEN** um usuário com role Médico conclui a autenticação
- **THEN** o sistema direciona para o shell do painel médico

#### Scenario: Financeiro conclui login
- **WHEN** um usuário com role Financeiro conclui a autenticação
- **THEN** o sistema direciona para o shell do painel financeiro

### Requirement: Não existe cadastro público nesta change
O sistema NÃO DEVE expor um fluxo público de criação de contas como parte desta capability inicial.

#### Scenario: Visitante acessa a área pública
- **WHEN** uma pessoa não autenticada navega pela aplicação
- **THEN** o sistema oferece autenticação, mas não oferece criação pública de conta

### Requirement: Bootstrap controlado do primeiro Administrador
O sistema DEVE fornecer um mecanismo de bootstrap manual, controlado e idempotente para criar o primeiro usuário Administrador quando ainda não existir um administrador, sem usar senha padrão hardcoded ou versionada.

#### Scenario: Primeiro bootstrap
- **WHEN** o bootstrap é executado com credenciais fornecidas por configuração segura e ainda não existe Administrador
- **THEN** o sistema cria exatamente um usuário Administrador com senha armazenada de forma segura

#### Scenario: Bootstrap repetido
- **WHEN** o bootstrap é executado novamente após já existir um Administrador correspondente
- **THEN** o sistema não cria uma conta duplicada nem substitui silenciosamente a credencial existente
