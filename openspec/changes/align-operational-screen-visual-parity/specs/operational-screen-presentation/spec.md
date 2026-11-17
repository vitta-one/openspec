## Purpose

Define a apresentação compartilhada das telas operacionais do Vitta-One, com variantes de navegação por perfil, estados reais do domínio e comportamento responsivo acessível.

## ADDED Requirements

### Requirement: Shell operacional preserva a variante visual de cada perfil
As rotas `/recepcao`, `/recepcao/agenda`, `/recepcao/pacientes`, `/recepcao/pacientes/novo`, `/recepcao/fila`, `/admin`, `/admin/funcionarios`, `/admin/funcionarios/novo`, `/admin/especialidades`, `/admin/horarios`, `/admin/configuracoes`, `/financeiro`, `/medico`, `/medico/agenda`, `/medico/pacientes` e `/medico/prontuarios` MUST usar a identidade visual canônica e os controles do shell autenticado. No primeiro carregamento autenticado por perfil, Recepção, Administração e Financeiro MUST iniciar com navegação compacta; Médico MUST iniciar com navegação expandida e marca Vitta-One. Uma escolha manual MUST ser preservada entre rotas do mesmo perfil e MUST poder ser alterada por controle acessível.

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
As 16 telas MUST manter rótulos semânticos, foco visível e ordem de teclado previsível. Em larguras de 320, 390, 768, 1024, 1440 e 1768 pixels, MUST evitar overflow horizontal do documento e adaptar listas e tabelas sem ocultar informações essenciais ou ações autorizadas. Movimentos não essenciais MUST respeitar `prefers-reduced-motion`. A comparação visual MUST cobrir cada uma das 16 rotas em viewport 1768×890 e registrar evidência responsiva nas larguras de 320, 390, 768, 1024 e 1440 pixels usando apenas dados sintéticos.

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
- **WHEN** a interface é comparada às referências locais durante a validação
- **THEN** as 16 rotas têm captura em 1768×890, há capturas responsivas nas cinco larguras definidas e nenhuma captura contém dados reais ou imagens de referência incorporadas à aplicação
