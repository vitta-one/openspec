## Why

O Vitta-One já permite que o Médico execute uma Consulta agendada, registre o Atendimento clínico e consulte o histórico concluído do paciente. O próximo passo do domínio é permitir que o Atendimento produza prescrições de forma estruturada, rastreável e imprimível, sem antecipar assinatura digital, exames ou integrações externas.

Hoje ainda não existe uma entidade persistente para receita/prescrição nem uma forma segura de associar medicamentos/itens ao Atendimento correto. Esta change cria essa capability mantendo o fluxo simples e coerente com o lifecycle já implementado.

## What Changes

- Criar uma entidade persistente de **Prescrição** vinculada ao `ClinicalCareRecord` e à mesma `Consultation`.
- Permitir **uma ou mais Prescrições** dentro do mesmo Atendimento clínico.
- Criar uma entidade persistente de **Item de Prescrição** pertencente a uma Prescrição.
- Cada item terá, nesta etapa:
  - medicamento/item;
  - orientação/posologia;
  - observações opcionais.
- Permitir ao Médico responsável:
  - criar nova Prescrição;
  - adicionar itens;
  - editar itens;
  - remover itens;
  - excluir Prescrição ainda editável;
  - editar observações gerais da Prescrição.
- Criar Prescrição já com o primeiro item válido para evitar documentos vazios persistidos.
- Impedir remoção do último item isoladamente; para eliminar o último item o Médico deve excluir a Prescrição inteira enquanto ela ainda for editável.
- Permitir mutações somente durante `Consultation.status == EM_ANDAMENTO`.
- Depois de `CONCLUIDA`, Prescrições e itens tornam-se somente leitura.
- Não criar status duplicado de “rascunho/finalizada”; a mutabilidade deriva do estado da Consulta.
- Integrar Prescrições ao histórico clínico concluído do paciente.
- Criar visualização protegida e pronta para impressão, sem gerar PDF nesta etapa.
- Exibir claramente na versão imprimível que **não há assinatura digital ZapSign nesta change**.
- Manter Admin QA como projeção somente leitura de Prescrições persistidas.
- Aplicar RBAC e ownership server-side em todas as leituras e mutações.
- Proteger conteúdo prescrito e dados pessoais contra exposição em logs e erros.

## Capabilities

### New Capabilities

- `clinical-prescription`: criação, edição, remoção, leitura histórica e visualização imprimível de Prescrições vinculadas ao Atendimento clínico.

### Modified Capabilities

Nenhuma capability consolidada precisa ter seus requisitos substituídos. A nova capability consome `clinical-care-record` e o lifecycle de Consulta já existentes.

## Scope Decisions

Para manter a entrega simples e não inventar regras clínicas:

- Prescrição só existe para Atendimento com `ClinicalCareRecord`;
- walk-in sem Consulta continua sem Prescrição nesta change;
- uma Consulta pode possuir várias Prescrições por meio do seu ClinicalCareRecord;
- uma Prescrição deve possuir pelo menos um item persistido;
- cada item usa texto livre e não possui catálogo de medicamentos;
- não há campos estruturados separados para dose, frequência, via ou duração;
- não há validação farmacológica;
- não há CID/ICD, autocomplete ou integração com base medicamentosa;
- o Médico pode criar/editar/remover Prescrições apenas durante `EM_ANDAMENTO`;
- após `CONCLUIDA`, o conteúdo é histórico somente leitura;
- a visualização de impressão é HTML/CSS protegida e não equivale a assinatura digital;
- impressão não gera PDF persistido;
- histórico mostra apenas Prescrições de Consultas concluídas;
- Admin QA permanece somente leitura.

## Out of Scope

- ZapSign e assinatura digital;
- validade jurídica da receita;
- certificado ICP-Brasil;
- PDF persistido;
- envio por e-mail;
- envio por WhatsApp;
- QR Code;
- catálogo de medicamentos;
- integração com farmácias;
- validação de interações medicamentosas;
- controle de medicamentos sujeitos a receita especial;
- numeração legal de receituário;
- exames;
- Cloudinary;
- financeiro/Asaas;
- prescrição para walk-in sem Consultation;
- edição pós-conclusão;
- reabertura de Consulta concluída.

## Impact

- Adiciona `Prescription` e `PrescriptionItem`.
- Adiciona migration incremental sobre `a6b3c9d2e5f1`.
- Evolui serviços/state/UI do Médico.
- Evolui a projeção de histórico clínico para carregar Prescrições concluídas.
- Adiciona uma rota/superfície de impressão protegida.
- Evolui Admin QA para projetar Prescrições reais somente leitura.
- Exige testes de autorização, imutabilidade, cardinalidade, concorrência, histórico e impressão protegida.
