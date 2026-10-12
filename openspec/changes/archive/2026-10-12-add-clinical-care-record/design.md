## Context

O lifecycle atual já garante:

```text
AGENDADA
  → CONFIRMADA + QueueEntry AGUARDANDO
  → EM_ANDAMENTO + QueueEntry EM_ATENDIMENTO
  → CONCLUIDA + QueueEntry FINALIZADO
```

O painel Médico conhece o paciente ativo, o profissional marcado, o horário da Consulta e o relato operacional recebido na Recepção. O que falta é persistir o conteúdo produzido pelo Médico durante o atendimento e tornar esse conteúdo reutilizável como histórico clínico.

A change deve adicionar essa camada sem transformar o Vitta-One em um prontuário complexo antes da hora.

## Goals / Non-Goals

**Goals:**

- garantir exatamente um Atendimento clínico por Consulta;
- criar o registro junto do início de uma Consulta agendada;
- permitir edição somente pelo Médico responsável e somente em `EM_ANDAMENTO`;
- persistir queixa principal, anamnese, diagnóstico e conduta/observações;
- permitir salvamento incremental;
- bloquear mutações após `CONCLUIDA`;
- exibir histórico clínico anterior do paciente durante o atendimento;
- manter histórico paginado e cronológico;
- expor os mesmos dados no Admin QA apenas como leitura;
- proteger conteúdo clínico de logs e erros.

**Non-Goals:**

- prescrição, exames, anexos e integrações;
- regras de obrigatoriedade clínica para concluir a Consulta;
- versionamento completo de prontuário;
- edição corretiva após conclusão;
- Atendimento sem Consulta;
- reabertura de Consulta.

## Decisions

### 1. Nova entidade `ClinicalCareRecord`

Criar uma entidade física própria para representar o Atendimento clínico.

Campos mínimos:

- `consultation_id`: FK `RESTRICT`, única e obrigatória;
- `patient_id`: FK `RESTRICT`, obrigatória;
- `doctor_user_id`: FK `RESTRICT`, obrigatória;
- `chief_complaint`: texto;
- `anamnesis`: texto;
- `diagnosis`: texto;
- `conduct_notes`: texto;
- `created_at`;
- `updated_at`.

Os quatro campos clínicos começam vazios e aceitam salvamento incremental.

Não armazenar `professional_id` no Atendimento porque o profissional já é fonte de verdade da Consulta. `doctor_user_id` é persistido para registrar quem realizou o atendimento e validar ownership de forma direta.

### 2. Uma Consulta possui no máximo um Atendimento

`consultation_id` recebe constraint unique.

A criação do registro ocorre quando uma Consulta agendada é chamada pelo Médico correto e transiciona de `CONFIRMADA` para `EM_ANDAMENTO`.

Na mesma transação:

1. QueueEntry é bloqueada;
2. Consulta é bloqueada e revalidada;
3. lifecycle muda para `EM_ANDAMENTO`;
4. ClinicalCareRecord é criado;
5. QueueEntry muda para `EM_ATENDIMENTO`;
6. commit único.

Se o registro já existir de forma inconsistente, a chamada é rejeitada e nenhuma transição parcial permanece persistida.

### 3. Walk-in permanece fora desta capability

QueueEntry sem `consultation_id` continua sendo walk-in.

Como esta change exige vínculo obrigatório com Consulta, o Médico continua podendo chamar/finalizar walk-ins, mas o formulário de Atendimento clínico não é criado para eles.

Uma change futura poderá definir se walk-in deve gerar Consulta, Atendimento independente ou outro vínculo. Esta change não decide isso.

### 4. O formulário é um rascunho durante EM_ANDAMENTO

Enquanto a Consulta estiver `EM_ANDAMENTO`, o Médico responsável pode salvar qualquer combinação dos quatro campos.

Regras:

- os campos podem estar vazios;
- cada campo recebe limite server-side de comprimento;
- whitespace é normalizado somente nas bordas, sem reescrever o conteúdo interno;
- salvar não muda Consulta nem QueueEntry;
- `updated_at` é atualizado somente em save válido.

A UI mantém estado “salvo” / “alterações não salvas”.

### 5. Finalização não exige conteúdo mínimo

Esta change não presume quais campos são clinicamente obrigatórios.

Portanto:

- Consulta pode ser concluída com registro vazio ou parcial;
- o servidor não bloqueia `EM_ANDAMENTO → CONCLUIDA` por conteúdo do Atendimento;
- a UI deve avisar de forma neutra quando o formulário possui alterações locais ainda não salvas;
- o botão “Finalizar atendimento” fica desabilitado enquanto houver alterações locais não salvas, evitando perda acidental no fluxo normal.

Chamadas diretas ao servidor continuam autorizadas a finalizar quando o lifecycle permitir; o Atendimento apenas se torna imutável após a conclusão.

### 6. Edição depende de ownership + estado atual

Para salvar:

1. sessão deve existir;
2. role deve ser `MEDICO`;
3. ClinicalCareRecord deve existir;
4. Consulta vinculada deve estar `EM_ANDAMENTO`;
5. o profissional da Consulta deve estar vinculado ao Médico autenticado;
6. `doctor_user_id` do registro deve ser o mesmo Médico.

Falha em qualquer etapa rejeita a mutação sem retornar conteúdo clínico desnecessário.

### 7. Consulta concluída transforma o Atendimento em histórico somente leitura

Não adicionar campo próprio de “finalizado” no ClinicalCareRecord.

A fonte de verdade é:

```text
Consultation.status == CONCLUIDA
```

Após a conclusão:

- save é rejeitado;
- `updated_at` não é reescrito;
- o registro entra na projeção de histórico clínico.

Isso evita duplicar lifecycle.

### 8. Histórico clínico é uma projeção, não uma nova entidade

“Prontuário” nesta etapa será uma consulta de ClinicalCareRecords concluídos do mesmo paciente.

Ordenação:

1. `Consultation.completed_at DESC`;
2. `Consultation.id DESC`.

Paginação server-side:
- 10 registros por página;
- página mínima 1;
- resultado inclui total e total de páginas.

Cada item mostra:
- data/horário da Consulta;
- profissional;
- queixa principal;
- anamnese;
- diagnóstico;
- conduta/observações.

Nenhum campo é editável no histórico.

### 9. Médico lê histórico somente no contexto do atendimento atual

O Médico autenticado pode carregar o histórico do paciente quando possui uma QueueEntry ativa vinculada a uma Consulta `EM_ANDAMENTO` daquele paciente.

Isso evita criar nesta change uma busca clínica global por CPF/nome para Médicos.

Ao perder/finalizar o atendimento ativo, o State limpa o conteúdo clínico sensível da sessão de UI.

### 10. O State Médico carrega atendimento atual e histórico juntos

Ao abrir/recarregar `/medico`:

- carregar QueueEntry ativa;
- se for walk-in, manter UI operacional atual e não buscar ClinicalCareRecord;
- se for Consulta agendada:
  - carregar ClinicalCareRecord atual autorizado;
  - carregar primeira página do histórico anterior;
  - preencher o formulário;
  - marcar estado como não alterado.

Após save:
- persistir;
- atualizar snapshot local;
- limpar dirty state.

Após finalização:
- limpar formulário e histórico sensível do State junto com o atendimento ativo.

### 11. UI permanece simples

No painel Médico, quando houver Consulta agendada ativa:

1. contexto do paciente já existente;
2. seção **Atendimento clínico** com quatro campos;
3. ações “Salvar atendimento” e “Finalizar atendimento”;
4. seção **Histórico clínico** abaixo, com cards/accordions somente leitura e paginação simples.

Não criar tabs profundas, wizard, editor rich text ou autosave nesta change.

Textarea deve preservar resize vertical e foco visível.

### 12. Admin QA projeta dados clínicos somente em modo local

No modo `VITTA_ONE_LOCAL_ADMIN_PREVIEW=true`, a tela de paciente pode substituir o placeholder de prontuário por uma projeção somente leitura de ClinicalCareRecords.

Regras:

- exigir a autorização já existente do Admin QA;
- nenhuma ação de edição;
- usar paginação;
- deixar claro que é uma projeção local de QA;
- fora do modo local, esta change não concede ao Administrador uma API geral de edição/leitura clínica.

### 13. Limites e validação de texto

Para evitar payloads ilimitados:

- `chief_complaint`: até 4.000 caracteres;
- `anamnesis`: até 12.000 caracteres;
- `diagnosis`: até 6.000 caracteres;
- `conduct_notes`: até 8.000 caracteres.

Limites devem existir no servidor e ser refletidos no formulário.

Erros devem identificar o campo de forma funcional sem ecoar o conteúdo enviado.

### 14. Dados clínicos não entram em logs

Handlers/serviços não devem registrar:

- conteúdo dos quatro campos;
- histórico clínico;
- CPF;
- payload completo de formulário.

Mensagens de erro devem ser genéricas ou descrever somente regra/estado.

### 15. Migration incremental

Criar revisão Alembic sobre a migration de `consultation-care-lifecycle`.

Upgrade:
1. criar tabela ClinicalCareRecord;
2. criar FKs;
3. criar unique em `consultation_id`;
4. criar índices úteis em `patient_id`, `doctor_user_id` e `updated_at`.

Downgrade:
1. remover índices/constraints;
2. remover tabela.

Não há backfill porque Consultas concluídas anteriores à change não possuem conteúdo clínico a inventar.

## Risks / Trade-offs

- **Registro vazio pode ser concluído:** escolha deliberada para não inventar obrigatoriedade clínica.
- **Sem histórico para Consultas antigas:** correto; o sistema não fabrica conteúdo retroativo.
- **Walk-in ainda sem Atendimento clínico:** mantém o modelo simples e expõe uma evolução futura real.
- **Sem versionamento de edições:** menor complexidade; `updated_at` registra apenas o último save.
- **Texto livre:** atende o MVP, mas não oferece semântica de CID/ICD.
- **Admin QA com dados sensíveis:** limitado ao modo local de QA e somente leitura; não vira permissão geral do papel Administrador.
