## MODIFIED Requirements

### Requirement: Especialidade é desativada sem exclusão física
O sistema MUST permitir que o Administrador altere uma especialidade entre ativa e inativa sem excluir fisicamente seu registro. A interface de gestão MUST exigir confirmação contextual antes de persistir uma alteração de situação, exibindo nome e situação atuais. Cancelar o diálogo MUST preservar integralmente o registro.

#### Scenario: Desativação
- **WHEN** o Administrador confirma a desativação de uma especialidade ativa
- **THEN** o registro permanece persistido, passa a ser identificado como inativo e deixa de poder ser selecionado em novas associações

#### Scenario: Reativação
- **WHEN** o Administrador confirma a reativação de uma especialidade inativa
- **THEN** a especialidade volta a poder ser selecionada em novas associações

#### Scenario: Desistência antes de alterar situação
- **WHEN** o Administrador cancela ou fecha o diálogo de alteração de situação
- **THEN** nenhuma mutação é executada e os vínculos históricos são preservados

### Requirement: Especialidades e profissionais possuem páginas completas de gestão
O sistema MUST oferecer páginas administrativas distintas para listagem, pesquisa, filtro de situação, paginação e operações de edição e ativação existentes. A listagem completa de especialidades MUST apresentar os registros autorizados em tabela semântica com colunas Especialidade, Situação e Ações, contagem dos resultados filtrados, busca combinada com situação, estados vazios adequados e opção de limpar filtros. O resumo recente do dashboard permanece distinto.

#### Scenario: Pesquisa sem resultado
- **WHEN** a pesquisa não encontra registros
- **THEN** a página apresenta estado vazio apropriado, sem apagar ou modificar dados

#### Scenario: Navegação e paginação
- **WHEN** o Administrador abre uma página completa e avança entre páginas
- **THEN** os controles informam estado atual e evitam navegação fora dos limites

#### Scenario: Combinar busca e situação
- **WHEN** o Administrador filtra o nome e seleciona a situação
- **THEN** a tabela apresenta somente a interseção dos registros persistidos, com contagem correta e retorno à primeira página

#### Scenario: Limpar filtros
- **WHEN** o Administrador limpa os filtros
- **THEN** busca e situação retornam ao padrão e a paginação volta a uma página válida

#### Scenario: Sem registros cadastrados
- **WHEN** a clínica não possui especialidades
- **THEN** a tela oferece o cadastro real sem exibir dados de exemplo como persistidos
