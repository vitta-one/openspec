## ADDED Requirements

### Requirement: Agenda administrativa em modo QA somente leitura
O sistema MUST disponibilizar ao Administrador autenticado a visualização da agenda em `/admin/agenda` somente quando o modo de QA local estiver explicitamente habilitado. Cada consulta MUST revalidar sessão, role e flag no servidor, sem permitir mutações de consulta ou slot.

#### Scenario: Preview disponível
- **WHEN** o Administrador autenticado abre a agenda com a flag QA habilitada
- **THEN** o sistema exibe a data atual no fuso da clínica e permite consultar médicos e meses a partir de dados persistidos.

#### Scenario: Acesso não autorizado
- **WHEN** o modo QA está desabilitado, a sessão expirou ou a role não é Administrador
- **THEN** nenhuma informação de agenda é retornada e o acesso é bloqueado ou redirecionado conforme a política de autenticação.

### Requirement: Agenda contextual por médico e dia
O sistema MUST filtrar slots e consultas persistidos em conjunto por profissional e mês, mostrar os dias com registros no calendário e detalhar o dia selecionado em ordem cronológica, com paginação em listas extensas.

#### Scenario: Sem registros na data
- **WHEN** a data selecionada não possui horários ou consultas autorizadas
- **THEN** o sistema exibe estados vazios compactos, sem produzir horários fictícios.

#### Scenario: Combinação de filtros
- **WHEN** o Administrador muda médico, mês ou dia
- **THEN** a interface limpa resultados anteriores durante o carregamento e mostra contagens derivadas apenas dos registros que correspondem aos filtros.

### Requirement: Projeção administrativa mínima de consulta
A visualização QA MUST exibir somente horário, médico e estado persistido das consultas; não MUST transmitir nome, CPF, sintomas, diagnóstico, prescrição ou demais campos clínicos do paciente.

#### Scenario: Consulta associada a paciente
- **WHEN** uma consulta persistida é incluída no preview
- **THEN** a projeção contém apenas os campos administrativos mínimos e não concede ao Administrador acesso ao fluxo de edição da Recepção.
