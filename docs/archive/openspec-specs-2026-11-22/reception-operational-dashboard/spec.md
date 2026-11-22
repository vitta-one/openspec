# reception-operational-dashboard Specification

## Purpose

Definir a operação diária da Recepção por consultas persistidas, com autorização server-side, busca controlada e sem inferir estado clínico.

## Requirements

### Requirement: A tabela do dia usa consultas reais no fuso da clínica
O sistema MUST listar as consultas persistidas cujo horário cai no dia atual do fuso configurado da clínica, ordenadas por horário e identificador. MUST incluir todos os estados persistidos, inclusive canceladas, sem inventar horários, disponibilidade ou dados de paciente.

#### Scenario: Banco vazio
- **WHEN** não há consultas no intervalo local do dia
- **THEN** a tabela informa que não há consultas para os filtros selecionados

#### Scenario: Limites de um dia local
- **WHEN** consultas existem antes, dentro e depois do intervalo local convertido para UTC
- **THEN** somente as consultas dentro do intervalo local são exibidas

#### Scenario: Situações persistidas
- **WHEN** há consultas agendadas, confirmadas, em andamento, concluídas e canceladas
- **THEN** cada linha exibe a situação persistida e as canceladas continuam visíveis

### Requirement: Dados da tabela ficam limitados à operação de recepção
Cada linha MUST conter apenas horário, nome e telefone do paciente, profissional, especialidades ativas associadas ao profissional e situação da Consulta. A projeção MUST NOT ler ou expor relatos, prontuário, diagnóstico, prescrição, prioridade ou notas clínicas. A busca MUST operar sobre nome, telefone e CPF dos pacientes das consultas daquele dia. CPF é usado somente para busca e não aparece na tabela.

#### Scenario: Telefone não informado
- **WHEN** uma Consulta pertence a paciente sem telefone cadastrado
- **THEN** a linha informa que o telefone não foi cadastrado, sem esconder o restante do compromisso

#### Scenario: Profissional sem especialidade ativa
- **WHEN** o profissional não tem especialidade ativa associada
- **THEN** a linha informa que a especialidade não está cadastrada

#### Scenario: Mais de uma especialidade
- **WHEN** o profissional possui múltiplas especialidades ativas
- **THEN** a linha exibe as especialidades registradas, sem afirmar que uma delas foi selecionada para aquela Consulta

#### Scenario: Busca por identidade operacional
- **WHEN** a Recepcionista busca por parte do nome, dígitos do telefone ou dígitos do CPF
- **THEN** somente consultas do dia associadas a pacientes correspondentes são retornadas

### Requirement: Filtro e paginação são aplicados no servidor
A interface MUST oferecer filtro por profissional e páginas de sete consultas; filtros e paginação MUST ser aplicados no banco antes da projeção exibida, com contagem real e ordenação estável. Trocar o filtro ou aplicar nova busca MUST voltar à primeira página.

#### Scenario: Profissional específico
- **WHEN** um profissional ativo é selecionado
- **THEN** são exibidas somente as Consultations do dia atribuídas a esse profissional

#### Scenario: Mais registros que uma página
- **WHEN** existem mais de sete consultas após os filtros
- **THEN** cada página mostra no máximo sete linhas e os controles refletem o total real

#### Scenario: Última página reduzida
- **WHEN** a última página tem menos de sete consultas
- **THEN** somente os registros restantes são exibidos e “Próxima” fica indisponível

#### Scenario: Atualização reduz resultados
- **WHEN** registros são removidos ou filtros reduzem o total enquanto uma página posterior está aberta
- **THEN** a consulta ajusta a página para a última página disponível sem exibir uma página inválida

### Requirement: Telefone do paciente é opcional e validado
O cadastro da Recepção MUST aceitar telefone brasileiro opcional com DDD, normalizar para dígitos e rejeitar valores preenchidos que não tenham 10 ou 11 dígitos. A migration MUST manter registros existentes válidos sem telefone.

#### Scenario: Novo paciente com telefone
- **WHEN** a Recepcionista cadastra paciente com telefone válido
- **THEN** o banco armazena somente os dígitos, e a tabela formata o telefone para leitura

#### Scenario: Cadastro sem telefone
- **WHEN** a Recepcionista não informa telefone
- **THEN** o cadastro é concluído e a tabela identifica que não há telefone

#### Scenario: Telefone inválido
- **WHEN** a Recepcionista informa telefone preenchido com comprimento inválido
- **THEN** o cadastro retorna validação segura e não persiste o paciente

### Requirement: Ações e permissões reutilizam os módulos existentes
O dashboard MUST permanecer protegido para a role Recepcionista; leituras da tabela MUST revalidar a sessão no servidor. A Agenda existente permanece responsável por localizar paciente para novos agendamentos, reagendar, cancelar e confirmar chegadas.

#### Scenario: Acesso à tabela
- **WHEN** uma sessão sem autorização de Recepcionista solicita os dados
- **THEN** o servidor nega a leitura antes de retornar nome, telefone ou compromissos

#### Scenario: Ação da tabela
- **WHEN** a Recepcionista escolhe abrir a Agenda a partir da tabela
- **THEN** a navegação segue para o módulo protegido e existente

### Requirement: A tabela se adapta a teclado e telas estreitas
A tela MUST manter rótulos acessíveis e foco visível na busca, filtro, paginação e ações. Em viewports estreitas, a tabela pode rolar horizontalmente dentro de uma região identificada, sem causar overflow horizontal do documento.

#### Scenario: Navegação por teclado
- **WHEN** a Recepcionista navega entre os filtros, ações e controles de página com teclado
- **THEN** os controles têm nome acessível e foco visível

#### Scenario: Tela estreita
- **WHEN** a tabela é exibida em viewport estreita
- **THEN** as colunas permanecem disponíveis em uma área de rolagem nomeada e o restante da página não transborda

### Requirement: Dashboard compartilha a ação de novo agendamento com a Agenda

O dashboard da Recepção MUST abrir o mesmo diálogo de agendamento da Agenda, preservando os indicadores e a visão semanal provenientes de consultas persistidas e atualizando as projeções após nova reserva.

#### Scenario: Nova consulta a partir da operação diária

- **WHEN** a recepcionista seleciona Nova consulta no dashboard
- **THEN** o diálogo de agendamento é aberto localmente e não cria uma segunda lógica de reserva

#### Scenario: Reserva concluída

- **WHEN** a Consulta é persistida pelo fluxo de agendamento
- **THEN** a visão semanal e os indicadores são atualizados usando dados persistidos e filtros existentes, sem duplicar consultas

### Requirement: O painel informa cancelamentos persistidos do dia
O painel de operação da Recepção MUST apresentar separadamente a quantidade de Consultas canceladas cuja data e horário pertencem ao dia atual no fuso configurado da clínica. A contagem MUST ser derivada dos registros persistidos e autorizada junto da projeção operacional existente; MUST NOT alterar a contagem de consultas não canceladas ou revelar identidade de paciente.

#### Scenario: Há consultas canceladas no dia
- **WHEN** o dia local possui uma ou mais Consultas canceladas
- **THEN** o painel apresenta a contagem real dessas Consultas em indicador próprio, além dos demais indicadores operacionais

#### Scenario: Não há cancelamentos no dia
- **WHEN** o dia local não possui Consulta cancelada
- **THEN** o indicador apresenta zero sem omitir sua categoria

#### Scenario: Limite do dia e autorização
- **WHEN** Consultas canceladas existem antes, dentro e depois do intervalo UTC correspondente ao dia local
- **THEN** somente as Consultas dentro do intervalo são contadas e o servidor disponibiliza o valor exclusivamente à role Recepcionista

### Requirement: Dashboard apresenta métricas agregadas de e-mails da agenda
A visão `/recepcao` MUST exibir contagens persistidas de notificações de agenda criadas nas 30 datas locais mais recentes, incluindo hoje: aceitas, entregues, falhas e pendentes/indeterminadas. Aceitação pelo Resend MUST ser distinguida de entrega confirmada. A projeção MUST exigir role Recepcionista no servidor e MUST retornar somente contagens, sem destinatários, conteúdo, identificadores de mensagens ou dados clínicos.

#### Scenario: Período sem notificações
- **WHEN** não há notificações de agenda criadas nas 30 datas locais mais recentes, incluindo hoje
- **THEN** os quatro indicadores mostram zero e não sugerem que houve envio

#### Scenario: Estados mistos do provedor
- **WHEN** notificações persistidas estão `ACCEPTED`, `DELIVERED`, `FAILED`, `PENDING`, `SENDING`, `UNKNOWN`, `NOT_CONFIGURED` ou `SUPPRESSED`
- **THEN** cada notificação é contada uma única vez: `ACCEPTED` em aceitas, `DELIVERED` em entregues, `FAILED` em falhas e os quatro estados restantes em pendentes/indeterminadas; `SUPPRESSED` fica fora das quatro contagens e aceitas não são apresentadas como entregues

#### Scenario: Acesso por outra role
- **WHEN** uma role diferente de Recepcionista solicita a projeção das métricas
- **THEN** o servidor nega a leitura antes de retornar os agregados

#### Scenario: Destinatário protegido
- **WHEN** a projeção das métricas é apresentada na Recepção
- **THEN** somente valores agregados são exibidos e nenhum endereço de e-mail ou corpo de mensagem é exposto

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

### Requirement: O preview administrativo em QA apresenta a operação da Recepção somente leitura
O sistema MUST disponibilizar `/admin/recepcao` apenas quando a flag local de QA estiver habilitada e a sessão válida pertencer ao Administrador. Cada recarga MUST revalidar a autorização no servidor antes de ler dados de pacientes, fila ou consultas. O preview MUST NOT disponibilizar eventos de criação, reavaliação, chamada, finalização, confirmação de chegada, cancelamento ou reagendamento.

#### Scenario: Acesso administrativo em QA
- **WHEN** o preview local está habilitado e uma sessão Administrador válida carrega a página
- **THEN** o sistema exibe uma projeção persistida somente leitura com identificação do modo QA

#### Scenario: Flag desativada ou sessão sem autorização
- **WHEN** a flag QA está desabilitada, a sessão expirou ou a role não é Administrador
- **THEN** a leitura é negada antes de retornar qualquer dado operacional protegido

### Requirement: Estado atual, histórico e agenda mantêm critérios temporais verificáveis
O preview MUST distinguir `AGUARDANDO` e `EM_ATENDIMENTO` atuais de `FINALIZADO` e `RETIRADO` por seus respectivos momentos de transição. As consultas MUST refletir registros agendados persistidos, com filtro de período em datas locais da clínica e de profissional, exibindo a situação persistida, sem inferir mudanças ou inventar horários. O preview MUST preservar a ordenação clínica já implementada para a fila aguardando e não pode alterar prioridade.

#### Scenario: Fila ativa e histórico coexistem
- **WHEN** há entradas aguardando e retiradas no banco
- **THEN** apenas aguardando e em atendimento compõem a fila ativa, enquanto retiradas aparecem no histórico do período

#### Scenario: Histórico cruza meia-noite UTC
- **WHEN** um evento é persistido em UTC e pertence ao dia local selecionado
- **THEN** a projeção inclui esse evento no dia local, exibe a hora no fuso da clínica e não transforma o instante armazenado

#### Scenario: Agenda sem consultas
- **WHEN** a consulta ao banco termina com sucesso e o período não possui consultas
- **THEN** o preview indica ausência de consultas para o período, não uma funcionalidade futura

#### Scenario: Falha na leitura
- **WHEN** o banco ou a projeção falha
- **THEN** o preview mostra erro contextual e não apresenta a falha como lista vazia

### Requirement: O preview transmite somente informação operacional mínima
A projeção MUST NOT expor CPF, relatos de sintomas, anamnese, diagnóstico, prescrição ou informação financeira. A agenda administrativa MUST conter apenas profissional, data/hora e situação. A página MUST permitir filtrar por período, prioridade e situação e limitar as listas sem falsificar contagens.

#### Scenario: Registro de fila contém sintomas
- **WHEN** a fila persistida contém relato clínico na entrada
- **THEN** a projeção da página não serializa o relato e identifica apenas paciente, prioridade, situação, horário e profissional pertinente

#### Scenario: Consulta com paciente cadastrado
- **WHEN** uma consulta é exibida na agenda administrativa
- **THEN** nenhum identificador ou dado clínico do paciente é enviado à lista da agenda

#### Scenario: Filtro aplicado
- **WHEN** o Administrador seleciona prioridade, situação ou período válido
- **THEN** os conjuntos exibidos e os indicadores aplicáveis refletem o filtro sem atribuir registros históricos à fila ativa
