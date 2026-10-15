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
