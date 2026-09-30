## Context

A autenticação/RBAC e o fluxo paciente/fila já estão consolidados. O painel Administrador continua como shell. O domínio global define Profissional e Especialidade como conceitos necessários para Agenda e Consulta, mas deliberadamente adiou a cardinalidade desse relacionamento até uma change que realmente precisasse dela.

Esta change é o momento em que a cardinalidade passa a ser necessária. Para evitar limitar um profissional a uma única área de atuação e evitar uma futura migração estrutural apenas para permitir uma segunda especialidade, a relação será muitos-para-muitos.

Agenda, disponibilidade e Consulta permanecem fora do escopo. O objetivo é somente produzir um diretório administrativo íntegro que a próxima change possa consumir.

## Goals / Non-Goals

**Goals:**

- persistir especialidades administráveis;
- persistir profissionais com identificador profissional único;
- associar um ou mais profissionais a uma ou mais especialidades;
- permitir vínculo opcional e único entre profissional e conta local `MEDICO`;
- permitir ativação/desativação lógica;
- disponibilizar essas operações somente ao Administrador;
- transformar `/admin` em uma área operacional acessível e responsiva para esta capability;
- preparar dados consistentes para agenda/agendamento futuros.

**Non-Goals:**

- criar ou editar contas de autenticação;
- agenda, disponibilidade, horários ou duração de consulta;
- agendamento e estados de Consulta;
- fila de atendimento;
- atendimento clínico ou prontuário;
- integrações externas;
- dashboards.

## Decisions

### 1. Especialidade é entidade persistente própria

Criar `Specialty` com nome de apresentação, chave normalizada para unicidade, estado ativo/inativo e timestamps técnicos.

O nome exibido preserva a escrita fornecida após limpeza de espaços. Uma chave normalizada em lowercase/casefold e espaços consolidados protege contra duplicidades como `Cardiologia`, ` cardiologia ` e variações equivalentes.

### 2. Profissional possui identificador profissional genérico

Criar `Professional` com nome, `registration_identifier`, estado ativo/inativo, vínculo opcional com `auth_users` e timestamps.

O identificador é tratado como um valor profissional único no contexto da clínica, sem hardcode de `CRM`, UF ou outro conselho. Uma change futura pode especializar esse dado caso haja requisito real.

### 3. Profissional e Especialidade formam relação muitos-para-muitos

Criar associação `ProfessionalSpecialty` com constraint única para `(professional_id, specialty_id)`.

Um profissional deve possuir pelo menos uma especialidade para ser salvo em estado válido. A mesma especialidade pode ser usada por vários profissionais. Especialidades inativas permanecem associadas historicamente, mas não podem ser incluídas em novas atualizações de associação.

A atualização das especialidades de um profissional será transacional: validar todo o conjunto antes de substituir associações para não deixar estado parcial em caso de erro.

### 4. Vínculo com usuário Médico é opcional, mas exclusivo

`Professional.user_id` é nullable e, quando preenchido, referencia `auth_users.id` com unicidade.

Antes de criar ou alterar o vínculo, o serviço verifica no servidor:
- a conta existe;
- a role é `MEDICO`;
- a conta ainda não pertence a outro profissional.

A FK/unique protege integridade concorrente; a regra de role permanece no serviço, porque o PostgreSQL não consegue expressar essa regra entre tabelas com uma constraint simples.

Desassociar uma conta não exclui a conta nem o profissional.

### 5. Desativação em vez de delete

Profissional e Especialidade possuem `is_active`. Não haverá delete físico no painel desta change.

Isso evita quebrar referências futuras e já estabelece o comportamento esperado para histórico quando Agenda/Consulta começar a referenciar esses registros.

### 6. Admin é a única role desta capability

Todo serviço de aplicação recebe o token de sessão e chama `require_role(..., Role.ADMINISTRADOR)` antes de consultar ou alterar os dados.

Nenhuma lista de profissionais, especialidades ou contas médicas disponíveis deve ser retornada por handler público ou role incompatível.

### 7. Contas Médicas disponíveis são projeção limitada

O formulário pode listar contas locais com role `MEDICO` para associação, mas a projeção retorna somente `id` e e-mail necessários à seleção. Hash de senha, tokens de sessão e outros campos nunca saem da camada de serviço.

Contas já associadas a outro profissional são apresentadas como indisponíveis ou omitidas; a validação final ainda acontece no servidor.

### 8. Painel Administrador evolui sem navegação global nova

Manter `/admin`.

O workspace terá duas áreas:
- **Especialidades:** criação, listagem, edição de nome e ativação/desativação;
- **Profissionais:** criação, listagem, edição, seleção múltipla de especialidades e vínculo opcional com uma conta Médica.

Ações destrutivas não existem; ativar/desativar é reversível. A interface deve deixar estados inativos textualmente claros e não depender apenas de cor.

### 9. Fluxos de edição são inline ou em painel contextual

Seguir a linguagem já estabelecida pelo Vitta-One: painéis simples, feedback inline, sem modal obrigatório e sem biblioteca adicional.

Listas permanecem verticais/cartões em telas estreitas. Em larguras maiores, especialidades e profissionais podem aproveitar duas colunas quando isso não reduzir legibilidade.

### 10. Migration incremental e reversível

Gerar uma revisão Alembic sobre `1e98cc2e0552`.

A ordem esperada:
1. `specialties`;
2. `professionals`;
3. `professional_specialties`.

O downgrade remove primeiro a associação e depois as entidades base. A migration deve ser validada em PostgreSQL 16 descartável.

## Risks / Trade-offs

- **Cardinalidade muitos-para-muitos adiciona uma tabela de associação:** custo pequeno e aceitável para evitar limitar profissionais a uma única especialidade.
- **Identificador profissional genérico:** evita regra regional prematura, mas exige refinamento futuro se validação por conselho/UF entrar no escopo.
- **Especialidade inativa ainda associada:** mantém rastreabilidade, mas a UI deve diferenciar claramente associação histórica inativa de opção disponível.
- **Conta Médica opcional:** permite preparar o diretório antes de provisionar login; fluxos clínicos futuros deverão exigir vínculo quando precisarem identificar o profissional autenticado.
- **Concorrência de unicidade:** nome normalizado, identificador profissional e `user_id` precisam de constraints no banco além da validação amigável no serviço.
