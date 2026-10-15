## MODIFIED Requirements

### Requirement: Indicadores operacionais usam somente registros persistidos
O sistema MUST computar consultas do dia não canceladas, chegadas confirmadas do dia, entradas aguardando, entradas em atendimento, entradas finalizadas no dia clínico e pendências de chegada usando os registros persistidos e as definições temporais existentes. MUST mostrar a origem/período de cada métrica e MUST NOT inferir espera, ausência, urgência ou conectividade.

#### Scenario: Primeira leitura sem registros
- **WHEN** o banco não contém Consultations nem QueueEntries e a primeira leitura termina com sucesso
- **THEN** todos os indicadores exibem zero e as listas mostram seus estados vazios

#### Scenario: Primeira leitura ainda não concluída
- **WHEN** o dashboard ainda não recebeu uma resposta bem-sucedida
- **THEN** apresenta carregamento e não confunde os valores iniciais zero com uma leitura vazia

#### Scenario: Dia local diferente do UTC
- **WHEN** consultas estão nos limites do dia local da clínica
- **THEN** os totais e pendências respeitam o intervalo convertido para UTC

#### Scenario: Métricas da fila
- **WHEN** existem entradas aguardando, em atendimento e finalizadas em dias diferentes
- **THEN** aguardando e em atendimento são estoque atual e finalizados contam somente pelo `finished_at` do dia clínico

### Requirement: Próximas consultas e prioridades não inferem dados
O sistema MUST apresentar até cinco Consultations `AGENDADA` futuras por data/hora, paciente, profissional e situação operacional, com link à Agenda existente, e MUST apresentar prioridades somente de entradas `AGUARDANDO` sem alterar sua classificação.

#### Scenario: Consulta futura elegível
- **WHEN** existem consultas futuras agendadas e canceladas
- **THEN** as próximas consultas mostram somente as agendadas, informam a situação e oferecem acesso à Agenda, sem dados clínicos

#### Scenario: Fila mista
- **WHEN** há pacientes aguardando e em atendimento com prioridades já atribuídas
- **THEN** somente entradas aguardando compõem a distribuição e nenhuma prioridade é recalculada

### Requirement: Atualização manual e falhas honestas
O sistema MUST disponibilizar atualização manual e horário da última leitura bem-sucedida, indicar carregamento, limpar dados protegidos em falha e permitir nova tentativa; MUST NOT apresentar zeros antes de uma leitura concluída como se fossem métricas atuais.

#### Scenario: Falha de atualização
- **WHEN** o banco falha durante uma leitura
- **THEN** o snapshot é limpo, a mensagem de erro oferece nova tentativa e nenhum número antigo é apresentado como atual

#### Scenario: Refresh durante leitura existente
- **WHEN** Recepcionista solicita atualização após o dashboard carregar
- **THEN** a interface identifica a atualização e mantém o horário da última leitura bem-sucedida até a resposta

## ADDED Requirements

### Requirement: Pendências de chegada direcionam para revisão sem inferir falta
O dashboard MUST apresentar total de consultas do dia clínico em status `AGENDADA` cujo horário passou sem confirmação e MUST listar até cinco itens mais antigos com horário, paciente e profissional, permitindo abrir a Agenda para revisão. MUST NOT confirmar chegada, cancelar, marcar falta ou indicar urgência automaticamente.

#### Scenario: Existem pendências de chegada
- **WHEN** há consultas `AGENDADA` de hoje com horário anterior à leitura
- **THEN** o dashboard apresenta a contagem total, no máximo cinco itens mais antigos e um link de revisão para a Agenda

#### Scenario: Mais de cinco pendências
- **WHEN** a contagem total supera os itens listados
- **THEN** o dashboard informa que a lista é limitada e preserva a contagem total real

#### Scenario: Sem pendências
- **WHEN** nenhuma consulta elegível aguarda confirmação de chegada
- **THEN** a seção mostra um estado vazio discreto

### Requirement: Ações rápidas do dashboard reutilizam as rotas da Recepção
O dashboard MUST oferecer acesso para agendar consulta e cadastrar paciente usando as rotas existentes, sem criar fluxos ou permissões paralelos.

#### Scenario: Acesso ao fluxo existente
- **WHEN** a Recepcionista escolhe uma ação rápida
- **THEN** é direcionada à Agenda ou ao módulo de Pacientes já protegido pela role

### Requirement: Dashboard preserva leitura em viewport estreita e teclado
Os cards de KPI MUST ser navegáveis por teclado, possuir foco visível e manter ação e informação acessíveis em viewports estreitas.

#### Scenario: Navegação por teclado
- **WHEN** a Recepcionista percorre os cards e links usando teclado
- **THEN** cada destino tem foco visível e rótulo compreensível

#### Scenario: Viewport estreita
- **WHEN** o dashboard é exibido em viewport estreita
- **THEN** os cartões e linhas se reorganizam sem ocultar métricas nem ações
