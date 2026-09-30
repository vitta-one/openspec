## Why

O Vitta-One já possui autenticação/RBAC, pacientes, fila operacional e diretório de profissionais/especialidades. O próximo elo do fluxo principal é a agenda: a clínica precisa declarar quando um profissional está disponível e a Recepção precisa conseguir criar, alterar e cancelar compromissos sem reservar o mesmo horário duas vezes.

O domínio confirma que uma Consulta relaciona Paciente + Profissional + Data/Horário e que o ciclo começa em `Agendada`, mas as regras completas de transição para `Confirmada`, `Em andamento` e `Concluída` permanecem deliberadamente abertas. Esta change implementa somente a parte de disponibilidade e agendamento necessária para chegar até uma Consulta agendada, sem antecipar o ciclo clínico posterior.

## What Changes

- Permitir que o Administrador crie, consulte, desative e reative slots futuros de disponibilidade para profissionais ativos.
- Representar disponibilidade como slots explícitos de data/hora, sem assumir duração fixa de 30/45/60 minutos nem regras recorrentes ainda não aprovadas.
- Permitir que a Recepcionista consulte a agenda por profissional e período.
- Permitir que a Recepcionista agende uma Consulta para um paciente existente em um slot disponível de um profissional ativo.
- Criar novas Consultas com estado inicial `AGENDADA`.
- Permitir reagendamento de Consulta `AGENDADA` para outro slot disponível, inclusive de outro profissional ativo, preservando o paciente.
- Permitir cancelamento de Consulta `AGENDADA`, preservando o registro histórico e devolvendo o slot à disponibilidade.
- Impedir reserva dupla do mesmo slot, inclusive sob concorrência.
- Impedir criação de slots e agendamentos no passado.
- Introduzir configuração explícita de timezone da clínica por nome IANA; persistir instantes em UTC e exibir/receber horários no timezone configurado.
- Evoluir os painéis `/admin` e `/recepcao` sem criar uma navegação global nova.
- Manter no modelo os cinco estados de Consulta já confirmados pelo domínio, mas esta change só executará transições relacionadas a `AGENDADA` e `CANCELADA`.

## Capabilities

### New Capabilities

- `appointment-scheduling`: disponibilidade por slots, agenda, criação de Consulta agendada, reagendamento, cancelamento e prevenção de conflito de horário.

### Modified Capabilities

Nenhuma capability existente precisa ter seus requisitos alterados. Esta capability consome Paciente, Profissional e RBAC já consolidados.

## Out of Scope

- regras de transição `AGENDADA → CONFIRMADA → EM_ANDAMENTO → CONCLUIDA`;
- confirmação de consulta;
- início/finalização de atendimento clínico;
- prontuário, diagnóstico, prescrição e exames;
- duração clínica da consulta e sobreposição por intervalos;
- disponibilidade recorrente semanal;
- geração em massa de slots;
- bloqueios por férias, feriados ou exceções recorrentes;
- lembretes por e-mail/WhatsApp;
- pagamento/Asaas;
- dashboards;
- alteração do paciente durante reagendamento.

## Impact

- Introduz modelos persistentes de slot de disponibilidade e Consulta.
- Adiciona uma migration incremental sobre a revisão atual do diretório profissional.
- Introduz configuração `VITTA_ONE_CLINIC_TIMEZONE` para interpretação consistente de datas/horários.
- Acrescenta gestão de disponibilidade ao painel Administrador.
- Acrescenta agenda/agendamento ao painel da Recepção.
- Exige locking/constraints PostgreSQL e testes concorrentes para garantir exclusividade do slot.
- Prepara a próxima change de ciclo de vida da Consulta e Atendimento sem decidir regras clínicas prematuramente.
