## ADDED Requirements

### Requirement: A home da Recepção disponibiliza a operação diária
A home protegida da Recepção MUST exibir a tabela autorizada de consultas do dia e seus filtros, além dos indicadores operacionais. A tela MUST manter somente uma ação primária de agendamento e reutilizar os fluxos autorizados de Agenda, Pacientes e Fila sem criar serviços paralelos.

#### Scenario: Consulta disponível na home
- **WHEN** a Recepcionista acessa `/recepcao` com uma consulta do dia persistida
- **THEN** a interface disponibiliza a linha da consulta e as ações compatíveis com sua situação

#### Scenario: Operação sem consultas hoje
- **WHEN** não há consultas para o dia e não há filtros ativos
- **THEN** o estado vazio informa apenas a ausência de consultas do dia, sem sugerir que a fila ou outros atendimentos estejam encerrados
- **AND** não há paginação desnecessária

#### Scenario: Filtro sem resultado
- **WHEN** a busca ou o filtro profissional não encontra consultas do dia
- **THEN** a interface apresenta um estado vazio específico com possibilidade de limpar filtros

### Requirement: Indicadores e tabela explicitam seus escopos
A home MUST identificar que os cinco indicadores representam a visão geral da clínica. Busca e filtro profissional MUST atuar somente na tabela de consultas do dia, sem sugerir que KPIs globais foram filtrados.

#### Scenario: Filtrar uma consulta por profissional
- **WHEN** a Recepcionista seleciona um profissional
- **THEN** somente a tabela é filtrada no servidor
- **AND** os indicadores permanecem globais e seu escopo é informado visivelmente

### Requirement: Atualização do dashboard preserva contexto e falhas
A home MUST mostrar carregamento inicial e erro de leitura distintos de estado vazio; MUST oferecer atualização manual com nome acessível, não executar duas atualizações manuais simultâneas e preservar os filtros quando os dados forem atualizados. A atualização automática MUST continuar usando o mecanismo existente.

#### Scenario: Falha de consulta de dados
- **WHEN** a leitura autorizada da Recepção falha
- **THEN** um erro visível é mostrado e dados protegidos anteriores não são mantidos como se estivessem atualizados

#### Scenario: Atualização manual durante carregamento
- **WHEN** a Recepcionista tenta atualizar enquanto já existe atualização em andamento
- **THEN** uma nova atualização manual não é iniciada
