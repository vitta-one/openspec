## ADDED Requirements

### Requirement: Painel administrativo exibe um resumo recente do diretório
O sistema MUST limitar o painel inicial às três especialidades e aos três profissionais mais recentemente criados, ordenados por data de criação decrescente e ID decrescente em empate, com dados reais e identidade de situação.

#### Scenario: Há mais de três especialidades
- **WHEN** o Administrador abre o painel com cinco especialidades persistidas
- **THEN** a superfície inicial apresenta apenas as três mais recentes e o link "Ver todas" abre a tela completa

#### Scenario: Há mais de três profissionais
- **WHEN** o Administrador abre o painel com cinco profissionais persistidos
- **THEN** o painel apresenta apenas os três mais recentes e o link "Ver todos" abre a tela completa

#### Scenario: Nenhum registro
- **WHEN** ainda não existem especialidades ou profissionais
- **THEN** o respectivo card mostra uma orientação clara com ação de cadastro

### Requirement: Especialidades e profissionais possuem páginas completas de gestão
O sistema MUST oferecer páginas administrativas distintas para listagem, pesquisa, filtro de situação, paginação e operações de edição e ativação existentes.

#### Scenario: Pesquisa sem resultado
- **WHEN** a pesquisa não encontra registros
- **THEN** a página apresenta estado vazio apropriado, sem apagar ou modificar dados

#### Scenario: Navegação e paginação
- **WHEN** o Administrador abre uma página completa e avança entre páginas
- **THEN** os controles informam estado atual e evitam navegação fora dos limites

### Requirement: Interações administrativas são acessíveis
Links e botões habilitados MUST oferecer feedback visual de interação, foco visível, tamanho adequado e ações por teclado, sem atribuir falsa interatividade a containers estáticos.

#### Scenario: Navegar sem mouse
- **WHEN** o Administrador usa Tab e Enter para acessar "Ver todas"
- **THEN** o foco está visível e a rota de destino abre corretamente
