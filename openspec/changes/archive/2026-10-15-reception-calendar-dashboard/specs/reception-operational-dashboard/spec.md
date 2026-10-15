## MODIFIED Requirements

### Requirement: Próximas consultas e prioridades não inferem dados
O sistema MUST apresentar um calendário visual dos próximos sete dias do fuso da clínica, permitir selecionar um dia e mostrar Consultations reais em ordem cronológica com hora, paciente, profissional e situação textual. Consultas canceladas permanecem visíveis e identificadas, mas não entram na contagem de consultas não canceladas. Em telas estreitas, a faixa de dias pode rolar horizontalmente sem causar overflow na página. Pendências de chegada e prioridades da fila ficam imediatamente após o calendário; os indicadores de aguardando/em atendimento não são repetidos na seção de prioridades. O dashboard MUST NOT presumir duração, disponibilidade, recorrência ou intervalo entre compromissos. As prioridades continuam vindo somente de QueueEntries em estado AGUARDANDO e não são recalculadas.

#### Scenario: Selecionar uma data
- **WHEN** a Recepcionista seleciona qualquer dia exibido nos próximos sete dias
- **THEN** a lista contém somente as consultas persistidas daquela data, ordenadas por scheduled_at e formatadas no fuso da clínica

#### Scenario: Consulta com diferentes situações
- **WHEN** a data contém consultas agendadas, confirmadas, em andamento, concluídas e canceladas
- **THEN** cada linha identifica sua situação em texto e compromissos cancelados não entram na contagem de consultas não canceladas

#### Scenario: Chegada não confirmada após o horário
- **WHEN** uma consulta de hoje segue AGENDADA depois do horário registrado
- **THEN** a interface pode identificá-la como “Chegada pendente” e encaminha a revisão manual para a Agenda, sem inferir falta

#### Scenario: Período sem consultas
- **WHEN** a data selecionada não possui Consultations
- **THEN** o calendário mantém o dia selecionado e mostra estado vazio sem compromissos ou disponibilidade inventados

#### Scenario: Viewport estreita e teclado
- **WHEN** a Recepcionista usa o calendário por teclado ou em viewport estreita
- **THEN** os dias mantêm nome, foco e estado selecionado acessíveis; em tela estreita, a faixa de dias pode rolar horizontalmente sem causar overflow na página e as linhas refluem
