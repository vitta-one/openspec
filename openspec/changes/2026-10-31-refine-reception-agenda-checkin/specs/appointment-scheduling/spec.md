# appointment-scheduling Specification

## ADDED Requirements

### Requirement: Agenda da Recepção apresenta um único período autorizado
O sistema MUST consultar consultas persistidas por Recepcionista autorizada e MUST usar o mesmo recorte de profissional e sete dias locais para calendário e listagem. MUST NOT preencher dias com horários fictícios nem devolver dados para perfil não autorizado.

#### Scenario: Filtro combinado
- **WHEN** a Recepcionista aplica profissional e data inicial
- **THEN** as duas visualizações exibem somente consultas daquele profissional nas mesmas sete datas

#### Scenario: Sem consultas
- **WHEN** o período não contém consultas
- **THEN** os dias exibem contagem zero e a lista apresenta estado vazio não técnico

#### Scenario: Acesso negado
- **WHEN** uma sessão sem role Recepcionista consulta a agenda
- **THEN** o servidor nega a leitura antes de retornar dados pessoais

### Requirement: Navegação semanal e seleção de dia
A agenda MUST navegar de sete em sete dias, voltar à data atual da clínica e aceitar início de período válido. MUST permitir selecionar e remover o filtro por dia, preservar ordenação cronológica e indicar consultas além da prévia.

#### Scenario: Próxima semana
- **WHEN** a Recepcionista avança sete dias
- **THEN** data inicial e final são recalculadas, a seleção anterior é removida e o profissional é preservado

#### Scenario: Filtrar e desfiltrar data
- **WHEN** um dia é selecionado e selecionado novamente
- **THEN** a lista primeiro mostra somente aquela data e depois retorna ao período inteiro

#### Scenario: Data inválida
- **WHEN** a data digitada é inválida
- **THEN** é exibido erro e não é solicitada consulta para um intervalo incorreto

#### Scenario: Muitas consultas
- **WHEN** um dia contém mais de duas consultas
- **THEN** a grade mostra duas prévias, o número restante e acesso à lista paginada

### Requirement: Ações de consulta preservam os fluxos existentes
A agenda MUST manter um único acesso à página dedicada de agendamento. Check-in, reagendamento e cancelamento MUST utilizar handlers existentes que revalidam role, recurso, estado e integridade no servidor. Estados MUST ter rótulo textual e ações acessíveis em mobile e por teclado.

#### Scenario: Chegada válida
- **WHEN** a Recepcionista confirma chegada de consulta elegível
- **THEN** a transição é persistida pelo serviço existente e agenda/fila são atualizadas

#### Scenario: Chegada duplicada
- **WHEN** uma consulta já confirmada recebe nova tentativa de check-in
- **THEN** o servidor rejeita a transição sem criar entrada duplicada

#### Scenario: Nova reserva
- **WHEN** uma consulta é criada no fluxo dedicado
- **THEN** o sistema retorna à agenda no período do agendamento recém-criado

#### Scenario: Mobile
- **WHEN** a agenda é exibida a 320 px
- **THEN** o calendário e cartões não provocam overflow horizontal da página e mantêm as ações autorizadas
