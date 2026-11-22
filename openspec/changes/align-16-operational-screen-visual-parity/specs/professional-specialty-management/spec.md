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

### Requirement: Diretórios administrativos mostram a paginação real dos resultados
O diretório de especialidades e o diretório completo de profissionais MUST exibir a faixa atual de resultados, um seletor de tamanho de página e controles de página anterior/atual/próxima. O tamanho MUST aceitar somente 10, 25 ou 50 itens, usar os registros carregados sob a autorização administrativa existente e reiniciar em 1 quando o tamanho mudar.

#### Scenario: Alterar o tamanho da página
- **WHEN** um Administrador escolhe um tamanho de página permitido
- **THEN** o diretório volta à página 1 e exibe a faixa correspondente aos resultados filtrados

#### Scenario: Rejeitar tamanho inválido
- **WHEN** chega um tamanho fora de 10, 25 ou 50
- **THEN** o estado de paginação permanece inalterado

### Requirement: Diretório de especialidades preserva a composição desktop compacta
Na referência desktop de 1768×890, o painel do diretório MUST manter seis linhas completas da tabela e a paginação visível na primeira dobra quando houver mais resultados. A rolagem vertical MUST ficar limitada à tabela, conservar o cabeçalho visível e permitir navegação por teclado; o restante da página não pode ser cortado.

#### Scenario: Há mais de seis especialidades na primeira página
- **WHEN** o Administrador abre o diretório no viewport de referência e existem mais de seis resultados
- **THEN** as seis primeiras linhas aparecem completas, a faixa de resultados e a paginação permanecem visíveis e a rolagem da lista é acessível por teclado
