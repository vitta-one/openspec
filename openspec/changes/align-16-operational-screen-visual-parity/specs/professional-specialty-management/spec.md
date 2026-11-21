## ADDED Requirements

### Requirement: Diretório de especialidades filtra vínculos profissionais
O diretório completo de especialidades MUST apresentar um controle acessível de filtros adicionais que permita distinguir especialidades com e sem profissionais vinculados, usando as associações persistidas carregadas por operações autorizadas. Limpar filtros MUST restaurar a lista e a página inicial.

#### Scenario: Filtrar especialidades vinculadas
- **WHEN** um Administrador seleciona “Com profissionais” nos filtros adicionais
- **THEN** a lista mostra somente especialidades que possuem ao menos um vínculo persistido

#### Scenario: Filtrar especialidades sem vínculos
- **WHEN** um Administrador seleciona “Sem profissionais” nos filtros adicionais
- **THEN** a lista mostra somente especialidades sem vínculos profissionais persistidos

#### Scenario: Remover filtro de vínculos
- **WHEN** o Administrador seleciona “Todas” ou limpa os filtros
- **THEN** a lista volta a considerar todas as especialidades que correspondem à pesquisa e ao filtro de situação
