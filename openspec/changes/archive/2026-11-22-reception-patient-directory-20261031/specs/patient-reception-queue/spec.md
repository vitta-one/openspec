## ADDED Requirements

### Requirement: Diretório operacional protegido de pacientes da Recepção
O sistema MUST oferecer à role Recepcionista uma listagem compacta dos pacientes persistidos com nome, telefone quando cadastrado e ação explícita de navegação à ficha individual. A leitura MUST revalidar a sessão e a role no servidor, MUST NOT incluir CPF em claro nem conteúdo clínico na projeção e MUST utilizar paginação persistente com ordenação determinística.

#### Scenario: Lista de pacientes cadastrados
- **WHEN** a Recepcionista autenticada acessa a página de pacientes
- **THEN** o sistema exibe somente pacientes persistidos, em tabela semântica com navegação "Ver detalhes" para a ficha autorizada

#### Scenario: Página com múltiplos registros
- **WHEN** a base possui mais registros que o tamanho de página
- **THEN** o servidor retorna somente a página solicitada, total real e ordenação estável por nome e identificador

#### Scenario: Página única
- **WHEN** os resultados cabem em uma página
- **THEN** a interface informa a quantidade com singular ou plural correto e oculta os controles de paginação

#### Scenario: Busca contextual
- **WHEN** a Recepcionista submete um nome, CPF ou telefone
- **THEN** o servidor normaliza a entrada, filtra somente registros autorizados e retorna à primeira página sem consultar a cada tecla

#### Scenario: Pesquisa vazia ou sem resultados
- **WHEN** a pesquisa não encontra resultados ou ainda não existem pacientes
- **THEN** a interface distingue esses estados e permite limpar a pesquisa ou iniciar o cadastro já existente

#### Scenario: Falha ao carregar
- **WHEN** a consulta falha por motivo operacional
- **THEN** os resultados desatualizados deixam de ser exibidos e a interface mostra mensagem acessível e ação para tentar novamente

#### Scenario: Sessão expirada ou role incompatível
- **WHEN** uma sessão expira ou um usuário de outro perfil solicita a listagem
- **THEN** o servidor nega a leitura, limpa os dados pessoais armazenados no State e direciona para o fluxo de autenticação ou acesso negado

#### Scenario: Responsividade e teclado
- **WHEN** a Recepcionista usa um dispositivo de largura reduzida ou navega por teclado
- **THEN** nome, contato e ação principal permanecem utilizáveis sem transbordo horizontal do documento, com labels e foco visível
