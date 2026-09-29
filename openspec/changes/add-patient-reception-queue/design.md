## Context

A capability `access-control` já está consolidada e fornece autenticação local, sessão revogável, roles fechadas e autorização server-side. Os painéis de Recepção e Médico ainda são shells sem comportamento de negócio.

O próximo incremento precisa suportar um fluxo de fila simples. A classificação clínica ocorre fora do Vitta-One: a aplicação somente persiste a prioridade informada pela operação. Isso evita transformar o sistema em mecanismo de triagem ou decisão médica.

A change deve permanecer separada do futuro conceito de `Consulta`: fila de atendimento imediato e consulta agendada possuem ciclos diferentes e não devem ser misturados antes das regras de agenda/consulta serem especificadas.

## Goals / Non-Goals

**Goals:**

- cadastrar um paciente mínimo e reutilizável;
- registrar uma passagem do paciente pela fila com sintomas e prioridade informados;
- manter ordenação determinística por prioridade e tempo;
- permitir reavaliação manual e retirada sem apagar histórico;
- permitir chamada concorrente segura do próximo paciente por Médicos;
- permitir finalização operacional do atendimento da fila;
- tornar `/recepcao` e `/medico` funcionais para esse fluxo;
- preservar RBAC server-side, privacidade, acessibilidade e responsividade.

**Non-Goals:**

- triagem automática, diagnóstico ou recomendação clínica;
- prontuário, anamnese ou histórico clínico longitudinal;
- prescrições, ZapSign, e-mail de documentos ou relatórios;
- exames/Cloudinary;
- agenda, agendamento e ciclo de Consulta;
- pagamentos/Asaas;
- painel público do paciente;
- profissionais, especialidades e roteamento automático por especialidade;
- escalonamento de prioridade por tempo de espera.

## Decisions

### 1. Paciente e passagem pela fila são conceitos separados

Criar um modelo persistente mínimo de `Patient` para identidade cadastral e um modelo `QueueEntry` para cada passagem pela fila. Sintomas, prioridade, horários e estado pertencem à passagem, pois podem mudar entre atendimentos sem alterar o cadastro base do paciente.

O modelo de paciente nesta change contém somente os dados necessários ao fluxo: nome, CPF normalizado e timestamps técnicos. Campos clínicos e cadastrais adicionais serão introduzidos somente quando requisitos futuros exigirem.

### 2. CPF normalizado e único

Persistir apenas dígitos do CPF, aplicar validação server-side dos dígitos verificadores e índice/constraint de unicidade. A interface pode aplicar máscara apenas como apresentação; a máscara não participa da regra de identidade.

Cadastro com CPF existente é rejeitado como duplicidade e a interface orienta o uso do paciente existente.

### 3. Prioridade é entrada operacional, não decisão do sistema

Definir enum fechado `VERMELHO`, `AMARELO`, `VERDE`. O sistema não calcula nem sugere prioridade.

A ordenação ativa é:

```text
VERMELHO → AMARELO → VERDE
dentro da prioridade: entered_at ASC → id ASC
```

O tempo de espera não modifica a prioridade armazenada. Reavaliações são ações explícitas da Recepcionista.

### 4. Ciclo de vida próprio da fila

Definir estados fechados:

```text
AGUARDANDO → EM_ATENDIMENTO → FINALIZADO
     └─────→ RETIRADO
```

Somente `AGUARDANDO` pode receber reavaliação ou retirada. `EM_ATENDIMENTO` é associado ao Médico que chamou. `FINALIZADO` e `RETIRADO` são terminais nesta change.

Não reutilizar os estados de `Consulta`, pois essa entidade futura permanece fora do escopo.

### 5. Chamada do próximo paciente deve ser atômica no PostgreSQL

A operação de "chamar próximo" será executada no servidor dentro de transação. A seleção considera somente `AGUARDANDO`, aplica a ordenação de prioridade e entrada e usa lock pessimista compatível com PostgreSQL (por exemplo, `FOR UPDATE SKIP LOCKED`) para impedir dupla atribuição quando dois Médicos chamarem simultaneamente.

A implementação deve encapsular essa regra em serviço testável em vez de distribuí-la na UI.

### 6. Médico responsável é a identidade autenticada

`QueueEntry` guarda o identificador do `auth_users` que chamou o paciente. Não será criado perfil de profissional nesta change. O vínculo é suficiente para provar autorização e impedir que outro Médico finalize o atendimento.

Especialidade e disponibilidade profissional ficam para change específica.

### 7. Operações da Recepção e Médico reutilizam RBAC existente

Todo handler que lê ou modifica dados da fila deve revalidar a sessão no servidor:

- cadastro, entrada, reavaliação e retirada: `RECEPCIONISTA`;
- chamada e finalização: `MEDICO`.

A visibilidade da UI nunca substitui essas verificações.

### 8. UI evolui os painéis existentes

Manter as rotas atuais `/recepcao` e `/medico`.

O painel da Recepção terá:
- formulário de cadastro/localização de paciente;
- formulário de entrada na fila;
- lista ordenada da fila ativa;
- ações de reavaliação e retirada;
- estados de loading, vazio, erro e sucesso.

O painel Médico terá:
- próxima fila elegível resumida;
- ação "Chamar próximo";
- atendimento ativo associado ao próprio Médico;
- ação de finalização;
- estados de loading, vazio, erro e sucesso.

Usar componentes Reflex e estilos já existentes. Não adicionar biblioteca de UI ou JavaScript customizado sem necessidade.

### 9. Dados sensíveis não aparecem em superfícies públicas ou logs

Sintomas e CPF são dados pessoais/sensíveis para o contexto da aplicação. Mensagens de erro não devem imprimir payloads, CPF completo, tokens ou sintomas. A UI de fila exige sessão e role apropriada.

### 10. Migração incremental e reversível

Adicionar uma nova revisão Alembic sobre a revisão de autenticação, sem recriar tabelas existentes. A migração deverá ser revisada e validada em PostgreSQL descartável antes de ser considerada pronta.

## Risks / Trade-offs

- **Concorrência na chamada:** mitigada por transação e lock de linha no banco; testes devem cobrir duas chamadas concorrentes.
- **CPF como chave cadastral:** simplifica deduplicação, mas não deve ser usado como chave primária nem exposto desnecessariamente.
- **Fila global sem especialidade:** reduz escopo e evita inventar regras de roteamento ainda não especificadas; a alocação por especialidade fica explicitamente adiada.
- **Ausência de prontuário/prescrição:** a finalização nesta change é operacional, não representa documentação clínica completa.
- **`FOR UPDATE SKIP LOCKED` é específico do banco alvo:** aceitável porque PostgreSQL já é uma decisão arquitetural do projeto; testes unitários puros podem usar SQLite somente para regras que não dependam do lock.
