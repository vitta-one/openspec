## Context

O Vitta-One possui hoje dois fluxos reais e independentes:

1. **Agenda**: Consulta ligada a Paciente + Profissional + slot, iniciando em `AGENDADA`.
2. **Fila operacional**: `QueueEntry` ligada a Paciente, sintomas, prioridade e estado `AGUARDANDO → EM_ATENDIMENTO → FINALIZADO`.

Essa separação foi deliberada na change de agendamento porque ainda não existia regra aprovada para transformar uma Consulta em atendimento. Esta change define somente a ponte mínima entre os dois fluxos.

O significado operacional de `CONFIRMADA` nesta etapa será específico e explícito: **a Recepção confirmou presencialmente a chegada do paciente e criou a entrada correspondente na fila**. Não significa confirmação por mensagem ou confirmação antecipada de presença.

Não será imposta janela de pontualidade nesta etapa. A Recepcionista decide manualmente quando confirmar a chegada de uma Consulta `AGENDADA`; o sistema não infere atraso, falta ou prioridade.

## Goals / Non-Goals

**Goals:**

- transformar uma Consulta `AGENDADA` em chegada confirmada de forma explícita;
- criar a entrada de fila correspondente atomicamente;
- impedir mais de uma entrada de fila por Consulta;
- preservar o fluxo walk-in existente;
- restringir Consulta agendada ao Médico vinculado ao profissional marcado;
- transicionar Consulta junto com chamada/finalização da fila;
- cancelar uma Consulta confirmada quando sua entrada ainda aguardando for retirada;
- manter estados de Consulta e fila consistentes sob concorrência;
- refletir o lifecycle nas telas de Recepção e Médico com UI simples;
- manter autorização e dados sensíveis no servidor.

**Non-Goals:**

- prontuário e dados clínicos do atendimento;
- confirmação remota/automática;
- janela de check-in;
- fila separada por agenda visual;
- autoentrada na fila;
- mudar prioridade automaticamente;
- reatribuir Consulta confirmada a outro profissional;
- transições após `CONCLUIDA`.

## Decisions

### 1. `CONFIRMADA` significa chegada presencial confirmada

Nesta change, a ação da Recepção será rotulada **Confirmar chegada**.

Ela é a única operação nova que executa:

```text
AGENDADA → CONFIRMADA
```

Não haverá botão genérico “Confirmar consulta”, porque isso poderia ser confundido com confirmação antecipada por telefone/mensagem.

A operação exige sintomas e uma das prioridades já existentes da fila (`VERMELHO`, `AMARELO`, `VERDE`). O sistema continua sem calcular triagem.

### 2. QueueEntry recebe vínculo opcional com Consulta

Adicionar `queue_entries.consultation_id` nullable com FK `RESTRICT` para `consultations.id`.

Regras:
- `NULL`: atendimento avulso/walk-in, comportamento atual;
- preenchido: entrada criada por chegada de Consulta agendada;
- índice/constraint unique em `consultation_id` quando não nulo garante no máximo uma entrada de fila por Consulta.

Não adicionar `queue_entry_id` também em Consulta; isso evitará relacionamento circular e duas fontes de verdade.

### 3. Consulta recebe timestamps explícitos de lifecycle

Adicionar a `Consultation`:
- `confirmed_at` nullable;
- `started_at` nullable;
- `completed_at` nullable.

`cancelled_at` já existe e continua sendo a fonte do cancelamento.

Cada timestamp é preenchido somente na transição correspondente e nunca reescrito por tentativa repetida/rejeitada.

### 4. Confirmar chegada é uma transação atômica

Fluxo:

1. revalidar sessão/role Recepcionista;
2. bloquear Consulta `FOR UPDATE`;
3. validar estado `AGENDADA`;
4. validar Paciente persistido;
5. validar Profissional ativo;
6. validar que `Professional.user_id` referencia conta com role `MEDICO`;
7. validar sintomas/prioridade;
8. verificar que ainda não existe QueueEntry para a Consulta;
9. criar QueueEntry `AGUARDANDO` com `consultation_id`;
10. alterar Consulta para `CONFIRMADA` e registrar `confirmed_at`;
11. commit único.

Violação concorrente de unicidade gera conflito de negócio seguro e rollback total.

O slot permanece `BOOKED`: a Consulta ainda está ocupando aquele compromisso, agora em andamento operacional.

### 5. Entrada agendada pertence ao Médico do profissional marcado

Para uma QueueEntry com `consultation_id`:
- o profissional da Consulta deve possuir `user_id`;
- esse usuário deve ter role `MEDICO`;
- apenas esse Médico considera a entrada elegível para contagem/chamada.

Entradas com `consultation_id = NULL` continuam walk-in e permanecem elegíveis segundo o comportamento atual.

Isso evita que uma Consulta de um profissional específico seja chamada por outro Médico apenas porque está no topo da fila global.

### 6. Elegibilidade é aplicada antes do locking da chamada

A seleção do próximo paciente deve continuar ordenada por prioridade → entrada mais antiga → id.

Para evitar `FOR UPDATE` problemático sobre joins opcionais, a query de QueueEntry usa uma condição de elegibilidade baseada em `EXISTS`/subquery:
- walk-in é elegível;
- agendada é elegível somente se o profissional da Consulta estiver vinculado ao Médico autenticado.

Depois da seleção da QueueEntry com `FOR UPDATE SKIP LOCKED`, a Consulta vinculada é bloqueada e revalidada antes da transição.

### 7. Chamada da fila transiciona a Consulta no mesmo commit

Para entrada agendada:

```text
QueueEntry:   AGUARDANDO → EM_ATENDIMENTO
Consultation: CONFIRMADA → EM_ANDAMENTO
```

O mesmo timestamp alimenta:
- `QueueEntry.called_at`;
- `Consultation.started_at`.

Se Consulta/Profissional/Médico estiver inconsistente, a chamada é rejeitada e a QueueEntry permanece aguardando.

Para walk-in, o comportamento atual é preservado sem Consulta.

### 8. Finalização da fila conclui a Consulta no mesmo commit

Para entrada agendada pertencente ao Médico autenticado:

```text
QueueEntry:   EM_ATENDIMENTO → FINALIZADO
Consultation: EM_ANDAMENTO → CONCLUIDA
```

O mesmo timestamp alimenta:
- `QueueEntry.finished_at`;
- `Consultation.completed_at`.

A checagem de ownership da QueueEntry continua obrigatória.

### 9. Retirada antes do atendimento cancela Consulta confirmada

Se uma QueueEntry agendada ainda está `AGUARDANDO`, a Recepção pode usar o fluxo existente de retirada com motivo.

No mesmo commit:

```text
QueueEntry:   AGUARDANDO → RETIRADO
Consultation: CONFIRMADA → CANCELADA
```

`withdrawn_at` e `cancelled_at` usam o mesmo instante.

O slot:
- retorna a `AVAILABLE` se ainda estiver no futuro e o profissional estiver ativo;
- caso contrário passa a `INACTIVE`.

Esse comportamento reutiliza a semântica já adotada pelo cancelamento de Consulta agendada.

Walk-ins retirados não afetam Consulta alguma.

### 10. Reavaliação não altera lifecycle da Consulta

Sintomas e prioridade podem mudar enquanto a QueueEntry está `AGUARDANDO`, conforme capability existente.

A Consulta vinculada continua `CONFIRMADA`.

Assim prioridade operacional e estado de compromisso permanecem conceitos separados.

### 11. Scheduling continua dono de reagendamento/cancelamento pré-chegada

Enquanto a Consulta está `AGENDADA`:
- reagendar/cancelar continua no fluxo `appointment-scheduling`.

Depois de `CONFIRMADA`:
- não pode ser reagendada;
- não pode ser cancelada pelo handler antigo;
- desistência antes da chamada acontece via retirada da QueueEntry.

`EM_ANDAMENTO` e `CONCLUIDA` não recebem cancelamento nesta change.

### 12. UI da Recepção mantém uma ação principal por etapa

Na lista de Consultas:
- `AGENDADA`: mostra “Confirmar chegada”, “Reagendar” e “Cancelar”;
- `CONFIRMADA`: mostra estado “Na fila”/“Confirmada” e direciona a operação para a seção da fila;
- `EM_ANDAMENTO`: somente leitura;
- `CONCLUIDA`: somente leitura;
- `CANCELADA`: somente histórico.

“Confirmar chegada” abre diálogo pequeno com:
- paciente/horário/profissional somente leitura;
- sintomas;
- prioridade;
- confirmar/cancelar.

Sem wizard ou calendário adicional.

### 13. UI da fila sinaliza origem sem duplicar informação

QueueEntry agendada recebe identificação curta “Consulta agendada”.

Na Recepção, a linha pode mostrar profissional/horário quando disponível.

No Médico, atendimento ativo mostra se veio de Consulta agendada e o horário originalmente marcado, sem criar formulário clínico novo.

### 14. Migration incremental preserva registros existentes

Gerar nova revisão sobre `9f7c2a1b4d6e`.

Upgrade:
1. adicionar timestamps nullable em `consultations`;
2. adicionar `consultation_id` nullable em `queue_entries`;
3. criar FK/índice/unique para o vínculo.

Downgrade remove vínculo/constraints antes dos timestamps.

Dados atuais continuam válidos:
- Consultas já existentes terão timestamps de lifecycle nulos;
- QueueEntries existentes terão `consultation_id = NULL` e permanecem walk-in.

## Risks / Trade-offs

- **CONFIRMADA passa a ter semântica operacional específica:** documentada explicitamente para evitar confusão com confirmação remota.
- **Sem janela de check-in:** evita inventar regra clínica/operacional ainda não aprovada; a decisão fica com a Recepção.
- **Profissional precisa de conta Médica vinculada para chegada:** evita criar Consulta confirmada impossível de ser chamada pelo Médico correto.
- **Walk-ins continuam globais:** preserva compatibilidade; separar walk-ins por especialidade/profissional exigiria nova regra.
- **Estados duplicados em Consulta e QueueEntry:** são intencionais porque representam conceitos diferentes, mas as transições acopladas precisam ser atômicas e bem testadas.
- **Retirada cancela Consulta confirmada:** é a interpretação mínima de desistência antes do atendimento e preserva histórico.
