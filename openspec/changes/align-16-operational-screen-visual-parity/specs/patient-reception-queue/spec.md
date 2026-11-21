## ADDED Requirements

### Requirement: O diretório da Recepção abre a ficha do paciente da linha selecionada
A lista de pacientes da Recepção MUST gerar a ação de detalhes a partir do identificador persistido da mesma linha que apresenta nome e telefone. Após ativar a ação, a rota e a ficha carregada MUST representar essa identidade e MUST continuar sujeitas à autorização server-side da Recepção.

#### Scenario: Abrir detalhes de um resultado da busca
- **WHEN** uma Recepcionista autenticada pesquisa pacientes e ativa “Ver detalhes” em uma linha
- **THEN** a rota de destino usa o identificador persistido dessa linha e a ficha exibe o nome do mesmo cadastro

#### Scenario: Sessão ou role sem acesso
- **WHEN** a sessão expira ou uma identidade sem role Recepcionista solicita a rota da ficha
- **THEN** o servidor nega o acesso conforme a autorização existente e não retorna dados do paciente

### Requirement: O diretório permite filtrar a disponibilidade de telefone e escolher o tamanho da página
A interface MUST oferecer um filtro recolhível de disponibilidade de telefone e tamanhos de página de 10, 20 e 30 registros. A busca, o filtro e a paginação MUST continuar aplicados no servidor após revalidar a role Recepcionista; alterar busca, filtro ou tamanho MUST reiniciar na primeira página.

#### Scenario: Filtrar cadastros com telefone
- **WHEN** uma Recepcionista escolhe “Com telefone” no painel “Mais filtros”
- **THEN** o servidor retorna somente pacientes persistidos com telefone não vazio e atualiza a contagem autorizada

#### Scenario: Filtrar cadastros sem telefone
- **WHEN** uma Recepcionista escolhe “Sem telefone” no painel “Mais filtros”
- **THEN** o servidor retorna somente pacientes persistidos sem telefone e preserva a pesquisa textual aplicada

#### Scenario: Ajustar tamanho da página
- **WHEN** uma Recepcionista seleciona 20 ou 30 itens por página
- **THEN** o servidor busca o tamanho solicitado, recalcula o total de páginas e exibe a primeira página
