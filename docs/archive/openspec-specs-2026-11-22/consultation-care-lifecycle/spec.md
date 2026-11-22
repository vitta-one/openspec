# consultation-care-lifecycle Specification

## Purpose

Conectar Consultas agendadas à fila operacional do Vitta-One de forma explícita e atômica, permitindo que a Recepção confirme a chegada do paciente e que o Médico inicie/conclua o compromisso correto sem misturar prontuário ou regras clínicas ainda não especificadas.

## Requirements


### Requirement: Recepção confirma chegada de Consulta Agendada
O sistema MUST permitir que a Recepcionista confirme a chegada de uma Consulta em estado `AGENDADA`. A operação MUST exigir sintomas e uma prioridade válida já suportada pela fila e MUST, na mesma transação, alterar a Consulta para `CONFIRMADA`, registrar o momento de confirmação e criar exatamente uma QueueEntry `AGUARDANDO` vinculada à Consulta e ao mesmo paciente.

#### Scenario: Chegada confirmada com sucesso
- **WHEN** a Recepcionista confirma a chegada de uma Consulta `AGENDADA`, informa sintomas e prioridade válidos e o profissional está apto a atender
- **THEN** a Consulta passa para `CONFIRMADA`, recebe `confirmed_at` e exatamente uma entrada `AGUARDANDO` é criada para o mesmo paciente

#### Scenario: Prioridade ou sintomas inválidos
- **WHEN** a Recepcionista tenta confirmar a chegada sem sintomas ou sem uma das prioridades permitidas
- **THEN** o servidor rejeita a operação e mantém Consulta e fila inalteradas

#### Scenario: Consulta não está Agendada
- **WHEN** a Recepcionista tenta confirmar chegada de Consulta em `CONFIRMADA`, `EM_ANDAMENTO`, `CONCLUIDA` ou `CANCELADA`
- **THEN** o servidor rejeita a operação e não cria nova entrada de fila

### Requirement: Profissional precisa estar apto para receber chegada
O sistema MUST permitir confirmar a chegada somente quando o profissional da Consulta estiver ativo e vinculado a uma conta existente com role Médico.

#### Scenario: Profissional ativo com conta Médica
- **WHEN** o profissional da Consulta está ativo e possui conta Médica vinculada
- **THEN** a chegada pode prosseguir se os demais dados forem válidos

#### Scenario: Profissional inativo
- **WHEN** o profissional foi desativado depois do agendamento
- **THEN** o servidor rejeita a chegada sem alterar Consulta ou fila

#### Scenario: Profissional sem conta Médica
- **WHEN** o profissional não possui conta Médica vinculada
- **THEN** o servidor rejeita a chegada e orienta a corrigir o vínculo antes de colocar o paciente na fila

### Requirement: Uma Consulta possui no máximo uma entrada de fila
O sistema MUST garantir por persistência que uma mesma Consulta esteja vinculada a no máximo uma QueueEntry, inclusive sob requisições concorrentes.

#### Scenario: Duas confirmações concorrentes
- **WHEN** duas requisições tentam confirmar simultaneamente a chegada da mesma Consulta `AGENDADA`
- **THEN** no máximo uma cria a QueueEntry e altera a Consulta; a outra recebe conflito sem duplicar o paciente na fila

#### Scenario: Vínculo já existente
- **WHEN** já existe QueueEntry associada à Consulta
- **THEN** o servidor rejeita qualquer tentativa de criar uma segunda entrada

### Requirement: Entradas walk-in continuam compatíveis
O sistema MUST permitir QueueEntry sem Consulta vinculada e MUST preservar o comportamento atual dessas entradas.

#### Scenario: Paciente avulso entra na fila
- **WHEN** a Recepcionista utiliza o fluxo existente de entrada avulsa
- **THEN** a QueueEntry é criada sem `consultation_id` e continua seguindo as regras atuais de prioridade, reavaliação, chamada e finalização

### Requirement: Consulta agendada é elegível somente ao Médico correto
Uma QueueEntry vinculada a Consulta MUST ser elegível para contagem e chamada somente pela conta Médica vinculada ao profissional daquela Consulta. QueueEntries walk-in MUST permanecer elegíveis segundo o comportamento existente.

#### Scenario: Médico correto consulta a fila
- **WHEN** existe QueueEntry agendada cujo profissional está vinculado ao Médico autenticado
- **THEN** essa entrada participa da contagem e da ordenação elegível desse Médico

#### Scenario: Outro Médico consulta a fila
- **WHEN** existe QueueEntry agendada vinculada a outro profissional
- **THEN** essa entrada não participa da contagem nem pode ser chamada pelo Médico autenticado

#### Scenario: Walk-in aguardando
- **WHEN** existe QueueEntry sem Consulta vinculada
- **THEN** ela continua elegível ao Médico segundo a regra atual da fila

### Requirement: Chamar entrada agendada inicia a Consulta atomicamente
Ao chamar uma QueueEntry vinculada a Consulta, o sistema MUST exigir que a entrada esteja `AGUARDANDO`, que a Consulta esteja `CONFIRMADA` e que o Médico autenticado corresponda ao profissional da Consulta. A mesma transação MUST alterar a fila para `EM_ATENDIMENTO`, a Consulta para `EM_ANDAMENTO` e registrar os timestamps correspondentes.

#### Scenario: Médico correto chama Consulta confirmada
- **WHEN** o Médico vinculado ao profissional chama a próxima entrada agendada elegível
- **THEN** a QueueEntry passa para `EM_ATENDIMENTO`, a Consulta passa para `EM_ANDAMENTO`, o Médico fica associado à entrada e os momentos de chamada/início são persistidos no mesmo commit

#### Scenario: Estado da Consulta está inconsistente
- **WHEN** a QueueEntry está aguardando mas a Consulta vinculada não está `CONFIRMADA`
- **THEN** o servidor rejeita a chamada e preserva os dois registros

#### Scenario: Concorrência na chamada
- **WHEN** duas requisições elegíveis disputam uma entrada
- **THEN** no máximo uma conclui a transição e nenhum estado de Consulta/fila diverge

### Requirement: Finalizar entrada agendada conclui a Consulta atomicamente
O sistema MUST concluir a Consulta vinculada somente quando o Médico responsável finalizar sua própria QueueEntry `EM_ATENDIMENTO`. A mesma transação MUST alterar a fila para `FINALIZADO`, a Consulta para `CONCLUIDA` e registrar os timestamps correspondentes.

#### Scenario: Finalização válida
- **WHEN** o Médico responsável finaliza uma entrada agendada em atendimento cuja Consulta está `EM_ANDAMENTO`
- **THEN** a QueueEntry passa para `FINALIZADO`, a Consulta passa para `CONCLUIDA` e os momentos de finalização/conclusão são persistidos no mesmo commit

#### Scenario: Consulta não está Em andamento
- **WHEN** a QueueEntry está em atendimento mas a Consulta vinculada não está `EM_ANDAMENTO`
- **THEN** o servidor rejeita a finalização sem alterar nenhum dos estados

#### Scenario: Médico diferente tenta finalizar
- **WHEN** uma identidade Médica diferente tenta finalizar a entrada
- **THEN** o servidor rejeita a operação e preserva fila e Consulta

### Requirement: Retirada de entrada agendada cancela Consulta confirmada
O sistema MUST permitir que a Recepcionista retire uma QueueEntry agendada somente enquanto ela estiver `AGUARDANDO`. A mesma transação MUST alterar a entrada para `RETIRADO`, registrar motivo/momento e alterar a Consulta de `CONFIRMADA` para `CANCELADA` com `cancelled_at`.

#### Scenario: Paciente desiste antes da chamada
- **WHEN** a Recepcionista retira uma entrada agendada aguardando com motivo válido
- **THEN** a QueueEntry passa para `RETIRADO` e a Consulta vinculada passa para `CANCELADA` no mesmo commit

#### Scenario: Slot ainda futuro
- **WHEN** a Consulta confirmada é cancelada pela retirada e o slot permanece futuro e elegível
- **THEN** o slot volta para `AVAILABLE`

#### Scenario: Slot já não é reutilizável
- **WHEN** o slot já passou ou o profissional não está ativo no momento da retirada
- **THEN** o slot não volta a aceitar nova reserva

### Requirement: Reavaliação não altera estado da Consulta
O sistema MUST permitir reavaliar sintomas/prioridade de QueueEntry agendada enquanto ela estiver `AGUARDANDO` sem modificar a Consulta vinculada.

#### Scenario: Prioridade de Consulta confirmada é reavaliada
- **WHEN** a Recepcionista altera sintomas/prioridade da QueueEntry agendada
- **THEN** a fila é atualizada e reordenada, enquanto a Consulta permanece `CONFIRMADA`

### Requirement: Reagendamento e cancelamento pré-chegada permanecem limitados a Agendada
O sistema MUST manter os handlers de scheduling restritos às Consultas `AGENDADA`. Depois da chegada confirmada, reagendamento e cancelamento direto de scheduling MUST ser rejeitados.

#### Scenario: Tentar reagendar Consulta confirmada
- **WHEN** a Recepcionista tenta usar o fluxo de reagendamento em Consulta `CONFIRMADA`
- **THEN** o servidor rejeita a operação e orienta o tratamento pelo fluxo da fila

#### Scenario: Tentar cancelar Consulta em andamento
- **WHEN** a Recepcionista tenta usar o fluxo de cancelamento de scheduling em Consulta `EM_ANDAMENTO`
- **THEN** o servidor rejeita a operação sem alterar a Consulta

### Requirement: Lifecycle registra timestamps sem reescrever histórico
O sistema MUST registrar `confirmed_at`, `started_at`, `completed_at` e `cancelled_at` somente quando a respectiva transição ocorrer com sucesso e MUST NOT sobrescrever timestamps por tentativa repetida ou operação rejeitada.

#### Scenario: Tentativa repetida de confirmar chegada
- **WHEN** a Consulta já está `CONFIRMADA`
- **THEN** `confirmed_at` permanece com o valor original

#### Scenario: Tentativa repetida de finalizar
- **WHEN** a Consulta já está `CONCLUIDA`
- **THEN** `completed_at` permanece com o valor original

### Requirement: Interfaces expõem o lifecycle sem inventar prontuário
A Recepção MUST oferecer “Confirmar chegada” em Consulta `AGENDADA`, solicitar sintomas/prioridade em diálogo acessível e exibir os estados posteriores como contexto operacional. O painel Médico MUST indicar quando o atendimento ativo deriva de Consulta agendada. Nenhuma dessas superfícies MUST criar campos clínicos de prontuário, diagnóstico ou prescrição.

#### Scenario: Recepção confirma chegada em tela estreita
- **WHEN** a Recepcionista usa viewport estreita e abre o fluxo de chegada
- **THEN** paciente, horário, sintomas, prioridade e ações permanecem legíveis e operáveis sem rolagem horizontal obrigatória

#### Scenario: Médico atende Consulta agendada
- **WHEN** o Médico chama uma QueueEntry vinculada
- **THEN** o painel identifica a origem agendada e mostra apenas contexto operacional já persistido

### Requirement: Lifecycle é protegido e transacional no servidor
O sistema MUST permitir confirmação/retirada/reavaliação à role Recepcionista e chamada/finalização à role Médico, revalidando sessão/role no servidor antes de retornar ou alterar dados. Transições acopladas de Consulta/fila MUST ocorrer na mesma transação.

#### Scenario: Role incompatível tenta confirmar chegada
- **WHEN** uma identidade sem role Recepcionista chama diretamente a operação
- **THEN** o servidor rejeita antes de retornar ou alterar dados protegidos

#### Scenario: Role incompatível tenta chamar Consulta agendada
- **WHEN** uma identidade sem role Médico chama diretamente a operação de fila
- **THEN** o servidor rejeita a operação e preserva todos os estados

#### Scenario: Falha durante transição acoplada
- **WHEN** qualquer validação, constraint ou lock impede uma transição entre Consulta e fila
- **THEN** a transação é revertida integralmente e nenhum estado parcial fica persistido
