## Context

A aplicação já cria exatamente um `ClinicalCareRecord` quando uma Consulta agendada entra em `EM_ANDAMENTO`. Esse registro pertence ao paciente, à Consulta e ao Médico responsável, pode ser editado durante o atendimento e se torna somente leitura após `CONCLUIDA`.

Prescrição é uma produção do Atendimento e deve usar o mesmo contexto de autorização e lifecycle. A change não deve introduzir um segundo modelo de atendimento, duplicar paciente/profissional nem antecipar assinatura ZapSign.

## Goals / Non-Goals

**Goals:**

- permitir múltiplas Prescrições por Atendimento;
- garantir que toda Prescrição pertença a um ClinicalCareRecord e à mesma Consulta;
- permitir múltiplos itens por Prescrição;
- oferecer CRUD simples enquanto a Consulta estiver `EM_ANDAMENTO`;
- impedir documentos vazios persistidos;
- tornar Prescrições imutáveis após `CONCLUIDA`;
- integrar Prescrições ao histórico concluído;
- fornecer visualização protegida e pronta para impressão;
- manter autorização/ownership no servidor;
- preservar conteúdo clínico/prescrito fora de logs.

**Non-Goals:**

- assinatura digital;
- PDF persistido;
- catálogo farmacológico;
- regras legais de receituário;
- envio externo;
- prescrição de walk-in;
- edição pós-conclusão.

## Decisions

### 1. Duas entidades: Prescription e PrescriptionItem

Criar:

`Prescription`
- `id`;
- `clinical_care_record_id`: FK obrigatória `RESTRICT`;
- `consultation_id`: FK obrigatória `RESTRICT`;
- `doctor_user_id`: FK obrigatória `RESTRICT`;
- `general_notes`: texto opcional;
- `created_at`;
- `updated_at`.

`PrescriptionItem`
- `id`;
- `prescription_id`: FK obrigatória;
- `medication_or_item`: texto obrigatório;
- `instructions`: texto obrigatório;
- `notes`: texto opcional;
- `created_at`;
- `updated_at`.

Não persistir `patient_id` no Prescription porque o paciente já é fonte de verdade do ClinicalCareRecord/Consultation.

### 2. Consultation é persistida também no Prescription como vínculo de integridade operacional

Embora `clinical_care_record_id` permita derivar a Consulta, `consultation_id` também é persistido para:

- autorização direta;
- filtros/history/print;
- validação explícita de consistência;
- evitar joins desnecessários em operações críticas.

O serviço MUST validar que:

```text
Prescription.consultation_id
==
ClinicalCareRecord.consultation_id
```

Não há duas fontes independentes de estado: o lifecycle continua exclusivamente em Consultation.

### 3. Uma Consulta pode possuir várias Prescrições

Não existe unique por `consultation_id` nem por `clinical_care_record_id` em Prescription.

Cada Prescrição representa um documento independente dentro do mesmo Atendimento.

A UI identifica documentos de forma ordinal apenas na apresentação:

```text
Prescrição 1
Prescrição 2
...
```

A numeração não é um identificador legal e não é persistida como regra de negócio.

### 4. PrescriptionItem usa texto livre simples

Campos:

- medicamento/item: até 300 caracteres;
- orientação/posologia: até 2.000 caracteres;
- observações: até 2.000 caracteres.

A aplicação não separa dose, via, frequência ou duração nesta etapa.

Não há parsing, validação farmacológica ou inferência clínica.

### 5. Prescrição é criada junto do primeiro item

Para evitar Prescription vazia:

`create_prescription` recebe:
- medicamento/item;
- orientação/posologia;
- observações do item;
- observações gerais opcionais.

Na mesma transação:

1. revalidar sessão/role Médico;
2. bloquear ClinicalCareRecord/Consultation;
3. validar `EM_ANDAMENTO`;
4. validar ownership;
5. criar Prescription;
6. criar o primeiro PrescriptionItem;
7. commit único.

Se o primeiro item for inválido, nada é criado.

### 6. Toda Prescrição persistida deve possuir pelo menos um item

O serviço não permite remover o último item isoladamente.

Quando existe apenas um item:
- ação “Remover item” é rejeitada/desabilitada;
- para apagar o documento, usar “Excluir prescrição”.

A exclusão da Prescrição é permitida somente em `EM_ANDAMENTO` e remove os itens filhos no mesmo fluxo controlado.

Para essa finalidade, `PrescriptionItem.prescription_id` usa FK com `ON DELETE CASCADE`; a autorização da exclusão continua no serviço.

Após `CONCLUIDA`, nenhuma exclusão é permitida.

### 7. Mutabilidade deriva da Consultation

Não adicionar coluna de status em Prescription.

Regras:

- `EM_ANDAMENTO`: criar, editar, adicionar/remover item, editar observações e excluir documento;
- `CONCLUIDA`: somente leitura;
- qualquer outro estado: mutação rejeitada.

Isso mantém uma única fonte de verdade do lifecycle.

### 8. Ownership usa o Médico responsável do Atendimento

Em toda mutação:

- sessão válida;
- role `MEDICO`;
- Prescription pertence ao ClinicalCareRecord;
- ClinicalCareRecord pertence à Consultation;
- `Prescription.doctor_user_id == ClinicalCareRecord.doctor_user_id`;
- profissional da Consultation está vinculado ao mesmo Médico autenticado;
- Consultation está `EM_ANDAMENTO`.

Falhas de autorização não retornam o conteúdo da Prescrição.

### 9. Atualizações usam locking

Criar/editar/excluir Prescrição ou item MUST revalidar o contexto sob lock.

- Prescription: `FOR UPDATE`;
- item alvo: `FOR UPDATE` quando aplicável;
- Consultation/ClinicalCareRecord revalidados antes da mutação.

Saves concorrentes devem terminar em estado íntegro, sem itens órfãos ou documento vazio.

Não é necessário versionamento otimista nesta etapa.

### 10. Observações gerais pertencem ao documento

`general_notes` é opcional e possui limite de 4.000 caracteres.

Serve para instruções gerais que não pertencem a um item específico.

Não é obrigatório criar uma Prescrição separada apenas por observação.

### 11. Histórico clínico inclui Prescrições concluídas

A projeção já existente de histórico clínico deve passar a incluir Prescrições vinculadas ao ClinicalCareRecord de cada Consulta `CONCLUIDA`.

Cada Prescription histórica retorna:
- id;
- data de criação;
- observações gerais;
- itens na ordem de criação.

Cada item retorna:
- medicamento/item;
- orientação/posologia;
- observações.

A implementação deve evitar N+1 descontrolado, preferindo carregamento/batch por conjunto de ClinicalCareRecord ids da página atual.

Prescrições de Consulta ainda em andamento não entram no histórico anterior; aparecem na seção editável do atendimento atual.

### 12. UI do Médico usa uma seção separada “Prescrições”

No atendimento agendado ativo:

1. Atendimento clínico;
2. Prescrições;
3. Histórico clínico.

A seção Prescrições contém:
- botão “Nova prescrição”;
- cards dos documentos atuais;
- itens dentro de cada card;
- “Adicionar item”;
- editar item;
- remover item;
- editar observações gerais;
- excluir prescrição;
- visualizar/imprimir.

Não criar editor rich text, tabela densa ou wizard.

### 13. Criação e edição usam dialogs pequenos

“Nova prescrição” abre dialog com:
- medicamento/item;
- orientação/posologia;
- observações do item;
- observações gerais.

“Editar item” reutiliza dialog de item.

“Excluir prescrição” usa confirmação explícita.

Nenhuma ação destrutiva depende de `window.confirm`.

### 14. Dirty state continua independente do ClinicalCareRecord

O formulário de ClinicalCareRecord mantém seu dirty state atual.

Prescrições são salvas por operações explícitas próprias.

O botão “Finalizar atendimento” fica indisponível quando:
- o ClinicalCareRecord possui alterações locais não salvas; ou
- alguma operação de Prescrição está em andamento.

Não é necessário manter itens de Prescrição não persistidos fora de dialogs abertos.

### 15. Visualização de impressão é protegida e somente leitura

Adicionar uma superfície dedicada de impressão para Prescription persistida.

Comportamento:

- somente usuário autenticado;
- Médico só acessa Prescription da qual é o `doctor_user_id`/profissional responsável;
- acesso permanece permitido após `CONCLUIDA` para o Médico autor, facilitando reimpressão;
- Admin QA não recebe uma rota clínica geral de impressão;
- layout sem sidebar/topbar;
- marca Vitta-One;
- paciente;
- profissional;
- identificador profissional;
- data da Consulta;
- itens;
- observações gerais;
- aviso textual: **“Documento sem assinatura digital nesta etapa.”**

A view é HTML/CSS print-ready. Não gera arquivo PDF persistido.

### 16. Impressão não equivale a assinatura

Não adicionar:
- status `ASSINADA`;
- hash de assinatura;
- identificador ZapSign;
- QR Code;
- selo de validade;
- texto que implique assinatura digital.

A integração ZapSign será uma change posterior.

### 17. Histórico e impressão não inventam snapshot demográfico

A versão impressa usa os dados atuais persistidos no domínio:
- nome do paciente;
- profissional;
- identificador profissional;
- horário da Consulta.

Esta change não cria snapshot legal de dados do paciente/profissional.

Uma futura change de assinatura pode decidir se precisa de snapshot imutável.

### 18. Admin QA continua somente leitura

No modo local QA:

- Atendimento ativo pode mostrar Prescrições atuais;
- histórico do paciente pode mostrar Prescrições de Consultas concluídas;
- sem criar/editar/remover;
- sem API geral para papel Administrador fora da flag local.

### 19. Privacidade

Não registrar em logs:
- medicamento/item;
- orientação/posologia;
- observações;
- conteúdo completo da Prescrição;
- CPF.

Erros de validação informam apenas campo/regra.

Erros de banco não expõem nomes de constraints.

### 20. Migration incremental

Criar revisão Alembic sobre `a6b3c9d2e5f1`.

Upgrade:
1. criar `prescriptions`;
2. criar FKs/índices;
3. criar `prescription_items`;
4. criar FK `ON DELETE CASCADE` para itens;
5. criar índices para history/ownership.

Downgrade remove itens antes das Prescrições.

Não há backfill: Atendimentos anteriores não ganham Prescrições fictícias.

## Risks / Trade-offs

- **Texto livre não valida medicamento/posologia:** deliberado para o MVP.
- **Sem assinatura digital:** a impressão deve deixar isso explícito.
- **Exclusão física durante EM_ANDAMENTO:** aceitável para rascunho ainda não concluído; depois da conclusão não existe delete.
- **Sem snapshot legal:** suficiente antes da integração de assinatura.
- **Múltiplos documentos:** adiciona uma camada de UI, mas preserva o requisito aprovado de mais de uma Prescrição por Atendimento.
- **Reimpressão por id para o Médico autor:** amplia leitura histórica do próprio documento sem criar busca global de prontuário.
