## ADDED Requirements

### Requirement: Shell autenticado expõe navegação contextual e acessível
O shell compartilhado MUST mostrar apenas destinos existentes e autorizados à role atual; MUST indicar qual destino está ativo com `aria-current="page"`; e MUST preservar a indicação hierárquica de Administração sem atribuir estado atual ao ancestral. O recolhimento desktop MUST preservar nomes acessíveis dos destinos.

#### Scenario: Administrador acessa ficha de funcionário
- **WHEN** o Administrador acessa `/admin/funcionarios/novo` ou a ficha de um funcionário
- **THEN** Funcionários permanece destacado como destino atual e o contexto de Administração permanece identificável

#### Scenario: Administrador acessa especialidades
- **WHEN** o Administrador acessa `/admin/especialidades`
- **THEN** Especialidades é o destino ativo, e Visão geral não recebe `aria-current="page"`

#### Scenario: Menu mobile é fechado por teclado
- **WHEN** a pessoa abre a navegação temporária e pressiona Escape
- **THEN** o drawer fecha, devolve o foco ao controle de abertura e libera a rolagem do conteúdo

#### Scenario: O menu é recolhido no desktop
- **WHEN** a pessoa recolhe a sidebar em viewport desktop
- **THEN** ícones de destinos autorizados e seus nomes acessíveis continuam disponíveis

### Requirement: Preview local não amplia permissões clínicas
As visualizações operacionais de QA no menu do Administrador MUST aparecer somente com a configuração autorizada e MUST permanecer separadas das funções administrativas normais. Sua presença MUST NOT conceder leitura ou mutação clínica de outras roles.

#### Scenario: QA desabilitado
- **WHEN** o Administrador navega sem o modo local de QA habilitado
- **THEN** o menu não oferece os destinos de preview e as rotas de preview continuam bloqueadas pelo servidor

#### Scenario: QA habilitado
- **WHEN** o Administrador autorizado navega com a configuração local de QA habilitada
- **THEN** o menu distingue o grupo de inspeção local das tarefas administrativas e não oferece operações clínicas como permissão administrativa
