## ADDED Requirements

### Requirement: Preview local do Administrador navega pacientes persistidos com busca e paginação
Quando o modo local de QA do Administrador estiver explicitamente habilitado, a visualização de pacientes MUST apresentar somente pacientes persistidos, MUST oferecer uma única busca no topo por nome ou CPF mascarado e MUST paginar o conjunto filtrado sem inventar registros.

#### Scenario: Lista possui múltiplas páginas
- **WHEN** o conjunto filtrado ultrapassa o tamanho de página definido pela interface
- **THEN** a interface apresenta somente a página atual, informa página e total e permite navegar para páginas válidas

#### Scenario: Busca altera resultados
- **WHEN** o Administrador modifica a consulta de busca
- **THEN** o conjunto é filtrado por nome ou CPF mascarado e a navegação retorna para a primeira página

#### Scenario: Busca sem resultados
- **WHEN** nenhum paciente persistido corresponde à consulta
- **THEN** a interface apresenta estado de nenhum resultado sem simular pacientes

### Requirement: Preview local permite seleção contextual somente leitura
A visualização local de pacientes do Administrador MUST permitir selecionar no máximo um paciente por vez por meio de checkbox controlado e MUST apresentar contexto e ações somente leitura compatíveis com o modo QA.

#### Scenario: Selecionar paciente
- **WHEN** o Administrador marca o checkbox de um paciente
- **THEN** esse paciente passa a ser o único selecionado e a interface exibe seus dados disponíveis, histórico operacional persistido e ações somente leitura

#### Scenario: Selecionar outro paciente
- **WHEN** existe um paciente selecionado e o Administrador marca outro checkbox
- **THEN** a seleção anterior é substituída pela nova sem criar seleção em massa

#### Scenario: Limpar seleção
- **WHEN** o Administrador desmarca o paciente selecionado ou aciona “Limpar seleção”
- **THEN** o contexto de paciente é removido sem alterar qualquer dado persistido

#### Scenario: Permissões permanecem intactas
- **WHEN** o Administrador usa a barra contextual do preview
- **THEN** nenhuma ação exclusiva de Recepção ou Médico é disponibilizada ou executada e a autorização server-side existente permanece inalterada
