# reception-operational-dashboard Specification

## MODIFIED Requirements

### Requirement: Ações e permissões reutilizam os módulos existentes
O dashboard MUST oferecer um menu contextual por consulta com detalhes operacionais e somente as transições elegíveis ao status persistido. A chegada, o reagendamento e o cancelamento MUST reconsultar a agenda protegida no servidor antes de abrir o fluxo existente; a confirmação final MUST continuar usando os application services que revalidam autorização e transição. Detalhes MUST usar um snapshot autorizado e MUST NOT conter relato, prontuário, diagnóstico, prescrição, prioridade ou notas clínicas.

#### Scenario: Ação sobre consulta agendada
- **WHEN** a Recepcionista seleciona uma consulta `AGENDADA`
- **THEN** o menu oferece detalhes operacionais, confirmar chegada, reagendar e cancelar; cada transição abre o diálogo existente para a mesma consulta após revalidar seu estado

#### Scenario: Estado muda antes da ação
- **WHEN** a consulta deixa de estar `AGENDADA` antes da Recepcionista abrir chegada, reagendamento ou cancelamento
- **THEN** a transição não é oferecida ou aberta e a interface informa que o estado foi atualizado

#### Scenario: Ação sobre outros estados
- **WHEN** a consulta está `CONFIRMADA`, `EM_ANDAMENTO`, `CONCLUIDA` ou `CANCELADA`
- **THEN** o menu não oferece chegada, reagendamento ou cancelamento; detalhes operacionais permanecem disponíveis sem conteúdo clínico

#### Scenario: Acesso sem role
- **WHEN** uma sessão sem role Recepcionista invoca a leitura de detalhes ou tenta abrir uma transição
- **THEN** o servidor rejeita o acesso antes de retornar dados ou abrir o fluxo protegido

#### Scenario: Cancelamento
- **WHEN** a Recepcionista escolhe cancelar uma consulta elegível
- **THEN** o diálogo pede confirmação e o application service valida o estado atual antes de preservar o histórico e cancelar

#### Scenario: Acesso à tabela
- **WHEN** uma sessão sem autorização de Recepcionista solicita os dados
- **THEN** o servidor nega a leitura antes de retornar nome, telefone ou compromissos

#### Scenario: Ação da tabela
- **WHEN** a Recepcionista escolhe abrir a Agenda a partir da tabela
- **THEN** a navegação segue para o módulo protegido e existente

### Requirement: A tabela se adapta a teclado e telas estreitas
A interface MUST manter rótulos acessíveis e foco visível na busca, filtro, paginação e ações. O menu contextual MUST suportar teclado e seus diálogos MUST ser renderizados fora do menu. Em viewports de até 672 px, a lista MUST apresentar cartões com as mesmas informações operacionais e ações da tabela. Nenhuma largura MUST causar overflow horizontal do documento.

#### Scenario: Navegação por teclado
- **WHEN** a Recepcionista navega entre filtros, paginação e ações com teclado
- **THEN** os controles têm nome acessível e foco visível; Enter/Espaço abrem a ação e Escape fecha menu ou diálogo

#### Scenario: Mobile
- **WHEN** a tela é renderizada a 320 px ou 375 px
- **THEN** cada consulta aparece em cartão, todas as informações e ações permanecem acessíveis e o documento não rola horizontalmente

#### Scenario: Tablet
- **WHEN** a tela é renderizada a 768 px ou 1024 px
- **THEN** filtros e ações não são cortados e uma região delimitada contém eventual rolagem da tabela

#### Scenario: Desktop
- **WHEN** a tela é renderizada a 1280 px ou 1440 px
- **THEN** título, data, filtros e ações compõem um cabeçalho compacto acima da tabela, que mostra suas colunas sem rolagem horizontal

#### Scenario: Tela estreita
- **WHEN** a tabela é exibida em viewport estreita
- **THEN** as colunas permanecem disponíveis em uma área de rolagem nomeada e o restante da página não transborda
