## Context

O Vitta-One já possui pacientes persistidos, profissionais/especialidades administráveis e painéis separados por role. O domínio define Consulta como o compromisso clínico entre Paciente e Profissional em uma data/hora e exige prevenção de conflito para o mesmo profissional. Também confirma cinco estados de Consulta, mas deixa deliberadamente abertas as transições clínicas completas.

Nenhuma fonte do projeto define duração fixa de Consulta, intervalo entre atendimentos ou regra recorrente de disponibilidade. Para não transformar essas lacunas em decisões implícitas, esta change modela disponibilidade como slots discretos e explícitos de data/hora. Um slot representa um horário reservável, não um intervalo clínico; portanto, conflito nesta fase significa disputar o mesmo slot do mesmo profissional.

## Goals / Non-Goals

**Goals:**

- administrar slots futuros de disponibilidade de profissionais;
- consultar agenda por profissional e período;
- criar Consulta `AGENDADA` a partir de paciente + slot;
- impedir reserva dupla sob concorrência;
- reagendar Consulta `AGENDADA` atomicamente;
- cancelar Consulta `AGENDADA` preservando histórico e liberando slot;
- tornar timezone da clínica explícito;
- manter autorização server-side;
- adicionar UI responsiva/acessível aos painéis Administrador e Recepção;
- preparar o modelo para a futura change de ciclo de Consulta/Atendimento.

**Non-Goals:**

- duração de consulta e detecção de sobreposição por intervalos;
- disponibilidade recorrente, férias, feriados e geração em massa;
- transições para `CONFIRMADA`, `EM_ANDAMENTO` ou `CONCLUIDA`;
- atendimento clínico/prontuário;
- notificações;
- pagamento;
- dashboards.

## Decisions

### 1. Disponibilidade usa slots discretos

Criar `ProfessionalAvailabilitySlot` com:
- profissional;
- instante do slot;
- estado `AVAILABLE`, `BOOKED` ou `INACTIVE`;
- timestamps técnicos.

O banco impõe unicidade de `(professional_id, starts_at)`.

Essa modelagem resolve o requisito confirmado de impedir duas Consultas no mesmo horário sem assumir duração que o domínio ainda não definiu. Uma change futura pode introduzir duração/intervalo e migrar a regra de conflito para sobreposição temporal.

### 2. Consulta nasce como entidade persistente nesta change

Criar `Consultation` com:
- paciente;
- profissional;
- slot de disponibilidade;
- `scheduled_at`;
- estado;
- `created_at`, `updated_at`;
- `cancelled_at` nullable.

O estado aceita os cinco valores confirmados pelo domínio:
- `AGENDADA`;
- `CONFIRMADA`;
- `EM_ANDAMENTO`;
- `CONCLUIDA`;
- `CANCELADA`.

Os serviços desta change criam somente `AGENDADA` e executam somente `AGENDADA → CANCELADA`. Outros estados existem para compatibilidade futura, mas nenhuma transição adicional é exposta.

### 3. Um slot pode ter histórico de cancelamentos, mas só uma reserva ativa

Uma Consulta cancelada continua referenciando seu slot para preservar histórico. Por isso, `consultations.availability_slot_id` não pode ser simplesmente unique.

A integridade será protegida em duas camadas:
- locking pessimista no slot ao reservar/reagendar;
- índice único parcial PostgreSQL sobre `availability_slot_id` para Consultas cujo estado seja diferente de `CANCELADA`.

Assim um slot pode acumular Consultas canceladas ao longo do tempo, mas no máximo uma Consulta ativa.

### 4. Agendamento é uma transação atômica

Fluxo de criação:
1. revalidar sessão/role Recepcionista;
2. validar paciente;
3. bloquear o slot `FOR UPDATE`;
4. validar profissional ativo, slot futuro e estado `AVAILABLE`;
5. criar Consulta `AGENDADA`;
6. mudar slot para `BOOKED`;
7. commit único.

Erros de constraint são convertidos em conflito de horário seguro e a transação é revertida.

### 5. Reagendamento libera e reserva no mesmo commit

Somente Consulta `AGENDADA` pode ser reagendada nesta capability.

O serviço bloqueia a Consulta e os slots envolvidos. Para reduzir risco de deadlock, slots são bloqueados em ordem determinística de ID quando há dois registros distintos.

Somente depois de validar integralmente o destino:
- slot antigo retorna a `AVAILABLE` quando ainda ativo/futuro;
- novo slot passa a `BOOKED`;
- Consulta recebe novo `professional_id`, `availability_slot_id` e `scheduled_at`.

Qualquer falha faz rollback de todas as mudanças.

### 6. Cancelamento é histórico, não delete

Cancelar:
- exige estado `AGENDADA`;
- altera para `CANCELADA`;
- registra `cancelled_at`;
- devolve slot a `AVAILABLE` somente quando o slot continua futuro e não foi administrativamente inativado.

Nenhum registro é apagado.

### 7. Administração não pode invalidar uma reserva ativa

Administrador pode:
- criar slot futuro para profissional ativo;
- desativar slot `AVAILABLE`;
- reativar slot `INACTIVE` ainda futuro.

Slot `BOOKED` não pode ser desativado diretamente. O compromisso deve ser tratado pela Recepção, preservando separação de responsabilidades.

### 8. Profissional inativo não recebe novas reservas

Se um profissional for desativado depois que slots/Consultas já existem:
- histórico permanece intacto;
- nenhuma nova disponibilidade pode ser criada;
- nenhum slot desse profissional pode receber nova Consulta ou reagendamento;
- Consultas já agendadas não são canceladas automaticamente.

Uma change futura pode definir comportamento operacional adicional para esses casos.

### 9. Timezone da clínica é configuração explícita

Adicionar `VITTA_ONE_CLINIC_TIMEZONE` com nome IANA obrigatório para operações de agenda.

A UI trabalha com horário local da clínica. A camada server-side:
- valida o nome IANA com `zoneinfo.ZoneInfo`;
- converte entradas locais para timestamps timezone-aware em UTC antes de persistir;
- converte de UTC para o timezone da clínica ao apresentar agenda.

Não haverá fallback silencioso para timezone do servidor ou navegador.

### 10. Painel Administrador recebe gestão de disponibilidade

Manter `/admin` e o workspace existente.

Adicionar uma seção de disponibilidade com:
- seleção de profissional ativo;
- campo `datetime-local`;
- criação de slot;
- filtro por profissional/período;
- lista vertical de slots;
- ativar/desativar quando permitido.

Não introduzir calendário visual complexo nem dependência externa nesta fase.

### 11. Painel Recepção recebe Agenda antes da fila

Manter `/recepcao`.

Adicionar uma área operacional de agenda com:
- filtros de profissional e período;
- busca/seleção de paciente reutilizando a identidade mínima existente;
- lista de slots disponíveis;
- Consultas agendadas/canceladas;
- agendar;
- reagendar;
- cancelar.

A fila de atendimento existente continua independente e não será automaticamente alimentada pela Consulta nesta change.

### 12. Migration incremental e PostgreSQL como fonte de integridade

Gerar uma revisão Alembic sobre `c1fa18dd8731`.

Ordem:
1. `professional_availability_slots`;
2. `consultations`;
3. índices/constraints, incluindo índice único parcial de reserva ativa.

Downgrade remove primeiro constraints/índices dependentes e Consulta, depois slots.

## Risks / Trade-offs

- **Slots discretos não modelam duração:** deliberado; evita inventar regra clínica e resolve apenas conflito por horário explícito.
- **Timezone obrigatório aumenta configuração:** evita agenda depender do timezone incidental do servidor.
- **Consulta armazena `professional_id` e `scheduled_at` além do slot:** pequena duplicação intencional para tornar o compromisso autoexplicativo e facilitar histórico/consultas futuras.
- **Reagendar para outro profissional:** é permitido porque o novo slot é a fonte do novo profissional; o paciente permanece o mesmo.
- **Consultas canceladas compartilham o slot com reservas futuras:** exige índice parcial e testes PostgreSQL específicos.
- **Fila e Consulta continuam separadas:** integração automática entre chegada/agendamento/fila depende de regra operacional ainda não especificada.
