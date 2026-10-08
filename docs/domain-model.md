# Domain Model — Vitta-One

## 1. Visão conceitual

O modelo abaixo descreve os conceitos fundamentais do Vitta-One. Ele é **conceitual** e não define antecipadamente tabelas, chaves, ORM ou estrutura física do PostgreSQL.

```text
Usuário ── role ──► Administrador | Recepcionista | Médico | Financeiro

Paciente ───────────────► Consulta ◄────────────── Profissional
                              │                         │
                              │                         └── Especialidade
                              │
                              ├──► Pagamento
                              │
                              └──► Atendimento
                                      │
                                      ├── Diagnóstico
                                      ├── Prescrição
                                      └── Exame

Paciente ──► Prontuário ──► histórico cronológico de atendimentos
```

As cardinalidades que não estiverem explicitamente confirmadas devem ser definidas somente quando uma change precisar delas.

## 2. Usuário

Representa uma pessoa autorizada a utilizar o sistema segundo uma das roles previstas.

### Responsabilidade

Identificar o papel operacional do usuário e delimitar as funcionalidades e informações disponíveis para sua função.

### Role

As roles atuais são:

- Administrador;
- Recepcionista;
- Médico;
- Financeiro.

Cada role possui painel dedicado. Não existe granularidade adicional de permissões no escopo atual.

## 3. Paciente

Representa a pessoa atendida pela clínica.

### Principais informações conceituais

- dados cadastrais;
- informações de contato;
- informações relevantes ao atendimento;
- histórico de consultas;
- histórico de atendimentos.

### Relacionamentos

O paciente participa de consultas e possui histórico clínico organizado por meio do prontuário.

## 4. Profissional

Representa o profissional da clínica relacionado aos atendimentos e à agenda.

### Principais informações conceituais

- informações profissionais;
- especialidade;
- horários de atendimento;
- disponibilidade.

### Relacionamentos

Um profissional participa das consultas em que realizará o atendimento. O relacionamento exato entre profissionais e especialidades deverá ser refinado quando necessário, sem assumir antecipadamente uma cardinalidade não definida.

## 5. Especialidade

Representa uma área de atuação associada aos profissionais da clínica.

### Relacionamentos

Relaciona-se aos profissionais. A cardinalidade física desse relacionamento ainda não está definida.

## 6. Consulta

Representa o compromisso clínico agendado entre paciente e profissional em uma data e horário.

### Informações obrigatórias conceituais

- paciente;
- profissional;
- data/horário;
- estado atual.

### Ciclo de vida confirmado

```text
Agendada → Confirmada → Em andamento → Concluída
```

`Cancelada` é um estado adicional possível antes da conclusão. No fluxo atual, a Recepção confirma a chegada (`AGENDADA → CONFIRMADA`), o Médico responsável inicia o atendimento ao chamar a fila (`CONFIRMADA → EM_ANDAMENTO`) e conclui ao finalizar sua entrada (`EM_ANDAMENTO → CONCLUIDA`).

### Regras estruturais

- uma consulta deve possuir paciente, profissional e data/horário;
- um profissional não pode possuir consultas conflitantes no mesmo horário;
- uma consulta pode estar relacionada a pagamento;
- uma consulta pode originar um atendimento.

## 7. Atendimento

Representa as informações produzidas durante o atendimento médico relacionado a uma consulta.

### Principais informações conceituais

- queixa principal;
- anamnese;
- observações;
- diagnóstico;
- conduta;
- prescrições;
- exames;
- informações adicionais do atendimento.

### Regras estruturais

- o Atendimento clínico é representado por `ClinicalCareRecord`;
- cada Consulta possui no máximo um Atendimento clínico;
- o Atendimento deve estar relacionado à Consulta e ao paciente correspondentes;
- o Médico responsável é persistido no Atendimento;
- nesta etapa, Atendimento clínico existe somente para Consulta agendada que entrou em `EM_ANDAMENTO`;
- queixa principal, anamnese, diagnóstico e conduta/observações podem ser preenchidos incrementalmente;
- após a Consulta `CONCLUIDA`, o Atendimento torna-se somente leitura.

## 8. Prontuário

Representa a visão organizada do histórico clínico de um paciente.

### Responsabilidade

Apresentar registros anteriores de forma cronológica para apoiar a compreensão do histórico do paciente.

### Observação de modelagem

No escopo atual, prontuário **não é uma entidade física independente**. Ele é uma projeção paginada e cronológica dos `ClinicalCareRecord` associados a Consultas `CONCLUIDA` do paciente. Evoluções futuras podem ampliar essa visão sem duplicar a fonte de verdade do Atendimento.

## 9. Diagnóstico

Representa o diagnóstico registrado durante um atendimento.

Neste estágio não é necessário decidir se será uma entidade física independente ou parte do registro de atendimento.

## 10. Prescrição

Representa um documento produzido pelo Médico durante um Atendimento clínico.

### Estrutura confirmada

- um `ClinicalCareRecord` pode possuir zero, uma ou várias Prescrições;
- cada Prescrição pertence a um único `ClinicalCareRecord`, à mesma Consulta e ao Médico responsável;
- cada Prescrição persistida possui um ou mais itens;
- cada item registra medicamento/item, orientação/posologia e observações opcionais;
- a Prescrição pode possuir observações gerais;
- criação, edição e exclusão são permitidas somente enquanto a Consulta está `EM_ANDAMENTO`;
- após `CONCLUIDA`, Prescrição e itens tornam-se histórico somente leitura;
- a visualização atual é HTML/CSS pronta para impressão e não gera PDF persistido.

### Integração futura

A assinatura digital será realizada por meio do ZapSign em ambiente sandbox em change própria. A versão atual da Prescrição **não possui assinatura digital** e não apresenta selo, QR Code ou status de assinatura.

## 11. Exame

Representa um exame relacionado ao atendimento.

### Principais informações conceituais

- solicitação;
- tipo;
- observações;
- resultado;
- anexos.

### Integração e restrições

- anexos serão armazenados/gerenciados no Cloudinary;
- não haverá integração com laboratórios ou sistemas externos de exames.

## 12. Pagamento

Representa as informações financeiras associadas à operação da clínica.

### Responsabilidade

Permitir registro, consulta e acompanhamento básico a médio de pagamentos e valores.

### Relacionamentos

Um pagamento pode estar associado a uma consulta.

### Integração

O processamento associado aos pagamentos utilizará Asaas em ambiente sandbox.

## 13. Dashboard

Dashboard não é uma entidade independente do domínio. Ele representa uma projeção consolidada de informações já existentes no sistema, como consultas do dia, próximos atendimentos, quantidade de pacientes, consultas concluídas/canceladas e pagamentos.

## 14. Regras globais do domínio

1. Não permitir conflito de horário para o mesmo profissional.
2. Toda consulta deve relacionar paciente, profissional e data/horário.
3. Cada Consulta possui no máximo um Atendimento clínico, vinculado à Consulta, paciente e Médico responsável.
4. O prontuário deve projetar o histórico clínico concluído de forma cronológica, sem inventar registros.
5. O acesso funcional é determinado pela role do usuário e pelo painel correspondente.
6. Pagamentos podem ser associados às consultas.
7. Dashboards apenas consolidam dados existentes.
8. Integrações com laboratórios externos estão fora do escopo.

## 15. Decisões deliberadamente adiadas

Não definir neste documento:

- tabelas e colunas PostgreSQL;
- chaves primárias e estrangeiras;
- ORM ou estratégia de migração;
- cardinalidades ainda não confirmadas pelos requisitos;
- modelagem de exames, assinatura digital de prescrições e pagamentos;
- telas e ações ainda não especificadas das capabilities futuras.

Esses detalhes devem ser especificados nas changes em que se tornarem necessários.
