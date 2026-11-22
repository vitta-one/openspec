# operational-screen-presentation Specification

## Purpose

Estabelecer o comportamento compartilhado de apresentação, navegação, responsividade e estados acessíveis das telas operacionais sem alterar regras do domínio.

## Requirements

### Requirement: Shell operacional preserva a variante visual de cada perfil
As 16 rotas operacionais MUST usar a identidade visual canônica e os controles do shell autenticado. No primeiro acesso, a navegação MUST iniciar compacta para Recepção, Administração e Financeiro, e expandida com marca Vitta-One para Médico. Uma escolha manual MUST ser preservada entre rotas do mesmo perfil e MUST poder ser alterada por controle acessível.

#### Scenario: Abrangência das rotas operacionais
- **WHEN** a pessoa abre qualquer uma das rotas `/recepcao`, `/recepcao/agenda`, `/recepcao/pacientes`, `/recepcao/pacientes/novo`, `/recepcao/fila`, `/admin`, `/admin/funcionarios`, `/admin/funcionarios/novo`, `/admin/especialidades`, `/admin/horarios`, `/admin/configuracoes`, `/financeiro`, `/medico`, `/medico/agenda`, `/medico/pacientes` ou `/medico/prontuarios`
- **THEN** o shell autenticado mantém a identidade visual e os controles canônicos

#### Scenario: Abertura da navegação por perfil
- **WHEN** uma pessoa autenticada abre a primeira rota operacional de seu perfil em desktop
- **THEN** o shell apresenta a variante compacta para Recepção, Administração e Financeiro, e a variante expandida para Médico

#### Scenario: Alternância manual da navegação
- **WHEN** a pessoa aciona o controle de expandir/recolher navegação e depois navega para outra rota do mesmo perfil
- **THEN** a sidebar mantém o estado escolhido sem alterar a rota de destino, os dados carregados ou as permissões

#### Scenario: Navegação em viewport móvel
- **WHEN** a rota é exibida em viewport de até 1050 pixels
- **THEN** a sidebar usa o drawer móvel com nomes acessíveis, botão de fechamento e conteúdo sem overflow horizontal do documento

### Requirement: Conteúdo operacional mantém origem e estados do domínio
As telas MUST renderizar componentes e estados ligados às entidades e serviços autorizados de cada rota. Valores das referências visuais MUST NOT ser apresentados como registros persistidos; contagens vazias MUST mostrar zero ou estado vazio real, e mensagens de carregamento, erro, sem resultados e sucesso MUST corresponder à operação efetivamente realizada.

#### Scenario: Banco sem registros para o painel
- **WHEN** uma projeção autorizada não encontra registros para os filtros atuais
- **THEN** a tela mostra zero ou estado vazio, sem inserir registros de demonstração

#### Scenario: Filtro sem correspondências
- **WHEN** a pessoa aplica uma busca ou filtro sem resultado
- **THEN** a tela distingue ausência de resultado do estado sem cadastro e oferece somente ações que funcionem

#### Scenario: Operação com falha
- **WHEN** uma leitura ou mutação protegida falha
- **THEN** a tela não informa sucesso e não mantém dados protegidos de uma consulta anterior incompatível

### Requirement: Superfícies operacionais permanecem utilizáveis por teclado e responsivas
As 16 telas MUST manter rótulos semânticos, foco visível e ordem de teclado previsível. MUST evitar overflow horizontal do documento e adaptar listas e tabelas sem ocultar informações essenciais ou ações autorizadas. Movimentos não essenciais MUST respeitar `prefers-reduced-motion`. A comparação visual MUST cobrir as 16 rotas e os viewports definidos no cenário de evidência, utilizando somente dados sintéticos.

#### Scenario: Operação por teclado
- **WHEN** a pessoa navega por cabeçalho, filtros, tabelas, ações e diálogos usando teclado
- **THEN** os controles são identificáveis, o foco permanece visível e diálogos permitem fechamento conforme o padrão acessível da aplicação

#### Scenario: Tabela em viewport estreita
- **WHEN** uma tabela excede a largura disponível
- **THEN** a interface adapta a linha para cartão ou limita a rolagem à região da tabela, sem transbordar a página inteira

#### Scenario: Preferência por movimento reduzido
- **WHEN** o sistema operacional solicita movimento reduzido
- **THEN** transições decorativas são desativadas sem remover estados ou feedback

#### Scenario: Evidência visual de todas as telas
- **WHEN** a interface é comparada às referências locais durante a validação nos viewports 1768×890, 1440×900, 1024×768, 768×1024, 390×844 e 320×740
- **THEN** as 16 rotas têm captura em cada viewport, sem dados reais ou imagens de referência incorporadas à aplicação
