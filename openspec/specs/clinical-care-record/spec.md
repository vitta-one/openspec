# clinical-care-record Specification

## Purpose

Persistir o conteúdo clínico básico produzido durante uma Consulta em andamento, permitir edição segura pelo Médico responsável e formar um histórico cronológico somente leitura por paciente sem antecipar prescrição, exames ou integrações externas.

## Requirements


### Requirement: Consulta agendada em atendimento possui um único registro clínico
O sistema MUST possuir no máximo um ClinicalCareRecord por Consultation e MUST criar esse registro quando uma Consulta agendada é iniciada pelo Médico responsável.

#### Scenario: Médico chama Consulta confirmada
- **WHEN** o Médico vinculado ao profissional chama uma QueueEntry agendada elegível
- **THEN** a mesma transação que coloca a Consulta em `EM_ANDAMENTO` cria exatamente um ClinicalCareRecord ligado à Consulta, ao paciente e ao Médico autenticado

#### Scenario: Criação do registro clínico falha
- **WHEN** o ClinicalCareRecord não pode ser criado por conflito, constraint ou inconsistência
- **THEN** a chamada é revertida integralmente e Consulta/fila permanecem no estado anterior

#### Scenario: Atendimento clínico duplicado
- **WHEN** uma operação tenta persistir um segundo ClinicalCareRecord para a mesma Consultation
- **THEN** o banco e o serviço rejeitam a duplicação

### Requirement: Walk-in permanece sem registro clínico nesta change
O sistema MUST preservar o fluxo existente de QueueEntry sem Consultation e MUST NOT criar ClinicalCareRecord para walk-in nesta capability.

#### Scenario: Médico chama walk-in
- **WHEN** o Médico chama uma QueueEntry sem `consultation_id`
- **THEN** a fila continua seu lifecycle atual e nenhum ClinicalCareRecord é criado

### Requirement: Atendimento registra quatro áreas clínicas simples
O ClinicalCareRecord MUST suportar queixa principal, anamnese, diagnóstico e conduta/observações como texto livre.

#### Scenario: Médico salva conteúdo parcial
- **WHEN** o Médico responsável salva somente parte dos campos durante `EM_ANDAMENTO`
- **THEN** o sistema persiste os valores informados e mantém os demais campos vazios

#### Scenario: Campo excede limite
- **WHEN** qualquer campo clínico excede seu limite server-side
- **THEN** o sistema rejeita o save, mantém o registro anterior e informa qual campo precisa ser reduzido sem ecoar o conteúdo clínico

### Requirement: Somente o Médico responsável pode editar o Atendimento
O sistema MUST permitir mutação do ClinicalCareRecord somente para a conta Médica vinculada ao profissional da Consultation.

#### Scenario: Médico correto salva durante atendimento
- **WHEN** o Médico autenticado corresponde ao profissional da Consultation e a Consulta está `EM_ANDAMENTO`
- **THEN** o save é permitido

#### Scenario: Outro Médico tenta editar
- **WHEN** outra identidade Médica tenta salvar o ClinicalCareRecord
- **THEN** o servidor rejeita a mutação sem expor o conteúdo clínico

#### Scenario: Role não Médica tenta editar
- **WHEN** Administrador, Recepcionista ou Financeiro chama diretamente a operação de save
- **THEN** o servidor rejeita antes de retornar ou alterar dados clínicos

### Requirement: Atendimento só é editável enquanto a Consulta está Em andamento
O sistema MUST aceitar save somente quando a Consultation vinculada estiver `EM_ANDAMENTO`.

#### Scenario: Consulta concluída
- **WHEN** o Médico tenta salvar um ClinicalCareRecord cuja Consulta já está `CONCLUIDA`
- **THEN** o servidor rejeita a alteração e preserva os dados anteriores

#### Scenario: Consulta confirmada ainda na fila
- **WHEN** há tentativa de salvar antes da Consulta entrar em `EM_ANDAMENTO`
- **THEN** o servidor rejeita a operação

#### Scenario: Consulta cancelada
- **WHEN** há tentativa de salvar ClinicalCareRecord ligado a Consulta cancelada
- **THEN** o servidor rejeita a operação

### Requirement: Save clínico não altera lifecycle operacional
Salvar ClinicalCareRecord MUST NOT alterar estado ou timestamps da Consultation nem da QueueEntry.

#### Scenario: Médico salva Atendimento
- **WHEN** um save válido é concluído durante `EM_ANDAMENTO`
- **THEN** somente os campos do ClinicalCareRecord e seu `updated_at` são alterados

### Requirement: Conclusão não exige preenchimento mínimo
O sistema MUST NOT exigir preenchimento dos quatro campos clínicos para permitir a transição operacional válida de `EM_ANDAMENTO` para `CONCLUIDA`.

#### Scenario: Registro vazio
- **WHEN** o Médico finaliza uma Consulta em andamento cujo ClinicalCareRecord está vazio
- **THEN** a Consulta pode ser concluída conforme o lifecycle existente e o registro passa a ser somente leitura

#### Scenario: Registro parcial
- **WHEN** somente alguns campos foram preenchidos
- **THEN** a Consulta pode ser concluída e os valores existentes são preservados

### Requirement: UI protege alterações locais não salvas
A interface Médica MUST identificar alterações locais do formulário e MUST evitar finalização acidental pelo fluxo normal enquanto houver conteúdo não salvo.

#### Scenario: Formulário foi alterado
- **WHEN** o Médico modifica qualquer campo depois do último save
- **THEN** a UI indica alterações não salvas e desabilita a ação normal de finalizar até salvar ou restaurar o snapshot persistido

#### Scenario: Save concluído
- **WHEN** o servidor confirma o save
- **THEN** a UI atualiza o snapshot persistido, remove o estado dirty e reabilita a finalização

### Requirement: Histórico clínico usa somente Atendimentos concluídos
O sistema MUST projetar o histórico clínico a partir de ClinicalCareRecords cujas Consultations estejam `CONCLUIDA`.

#### Scenario: Paciente possui atendimentos anteriores concluídos
- **WHEN** o Médico carrega o histórico durante um atendimento ativo do mesmo paciente
- **THEN** os registros concluídos anteriores são retornados em ordem cronológica decrescente

#### Scenario: Registro da Consulta atual
- **WHEN** a Consulta atual ainda está `EM_ANDAMENTO`
- **THEN** seu ClinicalCareRecord não aparece como item do histórico anterior

#### Scenario: Consulta cancelada
- **WHEN** existe registro associado a estado não concluído
- **THEN** ele não participa da projeção do histórico

### Requirement: Histórico clínico é paginado no servidor
O sistema MUST paginar a projeção de histórico em páginas de 10 registros e MUST retornar total de registros e total de páginas.

#### Scenario: Histórico possui mais de dez registros
- **WHEN** o Médico solicita a primeira página
- **THEN** o servidor retorna no máximo 10 itens e informa que páginas adicionais existem

#### Scenario: Página fora do limite
- **WHEN** a UI solicita página menor que 1 ou superior ao total válido
- **THEN** o servidor normaliza/rejeita de forma segura sem retornar dados de outro paciente

### Requirement: Médico acessa histórico somente no contexto do paciente ativo
O sistema MUST retornar histórico clínico ao Médico somente quando ele possui uma QueueEntry ativa vinculada a uma Consultation `EM_ANDAMENTO` daquele paciente.

#### Scenario: Atendimento ativo válido
- **WHEN** o Médico responsável possui Consulta em andamento para o paciente
- **THEN** o histórico concluído desse paciente pode ser lido

#### Scenario: Médico pesquisa paciente sem atendimento ativo
- **WHEN** não existe atendimento ativo autorizado para aquele paciente
- **THEN** o servidor rejeita a leitura do histórico

#### Scenario: Médico tenta histórico de outro paciente
- **WHEN** o Médico possui atendimento ativo para um paciente mas solicita outro identificador
- **THEN** o servidor rejeita a leitura sem retornar registros

### Requirement: Painel Médico apresenta Atendimento atual e histórico de forma simples
A interface Médica MUST exibir o formulário clínico somente para atendimento ativo originado de Consulta agendada e MUST manter o fluxo walk-in existente sem formulário desta capability.

#### Scenario: Consulta agendada em andamento
- **WHEN** o Médico abre o painel com uma Consulta agendada ativa
- **THEN** visualiza contexto do paciente, quatro campos clínicos, ação de salvar, ação de finalizar e histórico anterior somente leitura

#### Scenario: Walk-in ativo
- **WHEN** o atendimento ativo não possui Consultation
- **THEN** o painel mantém o fluxo operacional atual e não mostra formulário ClinicalCareRecord

#### Scenario: Viewport estreita
- **WHEN** o formulário é usado em tela estreita
- **THEN** campos e ações permanecem em uma coluna, com labels, foco visível e sem rolagem horizontal obrigatória

### Requirement: Estado sensível é limpo quando o atendimento deixa de ser ativo
O State Médico MUST limpar conteúdo de formulário e histórico clínico quando não houver mais atendimento ativo autorizado.

#### Scenario: Médico finaliza Consulta
- **WHEN** a finalização é confirmada
- **THEN** o State remove do cliente os textos clínicos e o histórico carregado junto com o contexto do atendimento anterior

#### Scenario: Sessão expira
- **WHEN** a sessão deixa de ser válida
- **THEN** o State limpa os dados clínicos antes do redirecionamento de autenticação

### Requirement: Admin QA pode projetar histórico somente em modo local
O sistema MUST permitir que o preview local do Administrador exiba ClinicalCareRecords de forma somente leitura quando o modo Admin QA estiver explicitamente habilitado e a sessão for Administrador.

#### Scenario: Admin QA habilitado
- **WHEN** `VITTA_ONE_LOCAL_ADMIN_PREVIEW=true` e um Administrador autorizado seleciona um paciente no preview
- **THEN** o sistema pode exibir histórico clínico persistido paginado sem ações de edição

#### Scenario: Preview local desabilitado
- **WHEN** a flag de QA não está habilitada
- **THEN** esta capability não concede ao Administrador uma API geral de leitura clínica

### Requirement: Conteúdo clínico não é exposto em logs ou erros
O sistema MUST tratar os campos do ClinicalCareRecord como dados sensíveis e MUST NOT registrar payloads clínicos, CPF ou histórico em logs de aplicação, mensagens de erro ou telemetria.

#### Scenario: Save falha por validação
- **WHEN** um campo excede o limite
- **THEN** o erro identifica a regra/field sem repetir o texto clínico enviado

#### Scenario: Persistência falha
- **WHEN** uma constraint ou operação de banco falha
- **THEN** a resposta apresenta erro funcional sem stack trace, valor clínico ou detalhe interno de constraint

### Requirement: Criação e edição são protegidas por transação e locking
O sistema MUST usar transação de banco para criar o ClinicalCareRecord junto da transição para `EM_ANDAMENTO` e MUST revalidar estado/ownership sob lock antes de salvar alterações.

#### Scenario: Duas chamadas concorrentes disputam a mesma Consulta
- **WHEN** operações concorrentes tentam iniciar a mesma Consulta
- **THEN** no máximo um ClinicalCareRecord é criado e fila/Consulta/Atendimento permanecem consistentes

#### Scenario: Dois saves concorrentes
- **WHEN** duas requisições autorizadas tentam salvar o mesmo ClinicalCareRecord
- **THEN** o registro é serializado por locking e permanece em um estado válido sem criação duplicada
