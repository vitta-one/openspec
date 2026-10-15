# reception-operational-dashboard Specification

## Purpose

Definir as projeções e a agenda visual do dashboard da Recepção a partir de registros persistidos, com autorização server-side e sem inferir estado clínico.

## Requirements

### Requirement: Indicadores operacionais usam somente registros persistidos
O sistema MUST computar consultas agendadas hoje não canceladas, entradas aguardando, em atendimento, concluídas hoje, chegadas confirmadas hoje e pendências de chegada, observando o dia no fuso da clínica e sem duplicar eventos.

#### Scenario: Banco vazio
- **WHEN** não existem Consultations nem QueueEntries e a leitura termina com sucesso
- **THEN** os indicadores exibem zero e o dia selecionado do calendário mostra seu estado vazio

#### Scenario: Dia local diferente do UTC
- **WHEN** consultas existem nos limites do dia local
- **THEN** os totais e a data dos compromissos usam o intervalo convertido corretamente para UTC

### Requirement: Próximas consultas e prioridades não inferem dados
O sistema MUST apresentar os próximos sete dias do fuso da clínica e permitir selecionar qualquer um deles para consultar as Consultations persistidas por hora, paciente, profissional e situação. MUST NOT presumir duração, disponibilidade, recorrência ou intervalo entre horários. Consultas canceladas permanecem identificadas como canceladas e não entram na contagem das consultas não canceladas.

#### Scenario: Selecionar uma data
- **WHEN** a Recepcionista seleciona um dos sete dias do calendário
- **THEN** a lista mostra somente as consultas daquela data, em ordem de horário, e a seleção fica identificada para tecnologias assistivas

#### Scenario: Consulta com diferentes situações
- **WHEN** a data contém consultas agendadas, confirmadas, em andamento, concluídas ou canceladas
- **THEN** cada item mostra sua situação textual e canceladas não entram na contagem das consultas não canceladas

#### Scenario: Chegada não confirmada após o horário
- **WHEN** uma consulta de hoje está AGENDADA e seu horário passou no momento da leitura
- **THEN** o calendário pode identificá-la como “Chegada pendente” e oferece revisão manual pela Agenda, sem classificá-la como falta, urgência ou cancelamento

#### Scenario: Período sem consultas
- **WHEN** não há consultas registradas para a data selecionada
- **THEN** o calendário mantém a seleção e mostra um estado vazio honesto, sem horários ou disponibilidade fictícios

### Requirement: Pendências de chegada direcionam para revisão sem inferir falta
O dashboard MUST apresentar o total de consultas do dia clínico em status AGENDADA cujo horário passou sem confirmação e MUST listar até cinco itens mais antigos com horário, paciente e profissional, permitindo abrir a Agenda para revisão. MUST NOT confirmar chegada, cancelar, marcar falta ou indicar urgência automaticamente.

#### Scenario: Existem pendências de chegada
- **WHEN** há consultas AGENDADA de hoje com horário anterior à leitura
- **THEN** o dashboard apresenta a contagem total, no máximo cinco itens mais antigos e um link de revisão para a Agenda

#### Scenario: Mais de cinco pendências
- **WHEN** a contagem total supera os itens listados
- **THEN** o dashboard informa que a lista é limitada e preserva a contagem total real

#### Scenario: Sem pendências
- **WHEN** nenhuma consulta elegível aguarda confirmação de chegada
- **THEN** a seção mostra um estado vazio discreto

### Requirement: Prioridades da fila mantêm classificação operacional
O sistema MUST apresentar a contagem de prioridades somente para entradas AGUARDANDO, sem alterar sua classificação.

#### Scenario: Consulta cancelada e fila mista
- **WHEN** há consultas canceladas, pacientes em atendimento e prioridades já informadas pela operação
- **THEN** só os itens elegíveis entram nas projeções correspondentes e nenhuma prioridade é recalculada

### Requirement: Ações rápidas reutilizam as rotas da Recepção
O dashboard MUST oferecer acesso para agendar consultas, localizar/cadastrar pacientes, abrir a Agenda e abrir a Fila usando as rotas existentes, sem criar fluxos ou permissões paralelos.

#### Scenario: Acesso ao fluxo existente
- **WHEN** a Recepcionista escolhe uma ação rápida ou um link do calendário
- **THEN** é direcionada à Agenda, aos Pacientes ou à Fila já protegidos pela role

### Requirement: Atualização manual e falhas honestas
O sistema MUST disponibilizar atualização manual e horário da última leitura bem-sucedida, indicar carregamento, limpar dados protegidos em falha e permitir nova tentativa; MUST NOT apresentar zeros antes de uma leitura concluída como se fossem métricas atuais.

#### Scenario: Erro de leitura
- **WHEN** o banco está indisponível
- **THEN** nenhum número antigo é apresentado como atual e há um aviso

#### Scenario: Atualização da recepcionista
- **WHEN** a Recepcionista aciona Atualizar
- **THEN** o servidor revalida a sessão e recalcula as projeções e o calendário

### Requirement: Dashboard preserva leitura em viewport estreita e teclado
Os indicadores, a seleção de datas e as linhas de consulta MUST ser navegáveis por teclado, possuir foco visível e manter ações e informações acessíveis em viewports estreitas, sem overflow horizontal do documento.

#### Scenario: Navegação por teclado
- **WHEN** a Recepcionista percorre os cards, dias e links usando teclado
- **THEN** cada destino tem foco visível e cada dia comunica seleção e conteúdo compreensíveis

#### Scenario: Viewport estreita
- **WHEN** o dashboard é exibido em viewport estreita
- **THEN** os cartões, dias e linhas se reorganizam sem ocultar métricas nem ações
