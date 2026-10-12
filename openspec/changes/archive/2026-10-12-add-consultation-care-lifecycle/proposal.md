## Why

O Vitta-One já permite agendar, reagendar e cancelar Consultas em estado `AGENDADA`, enquanto a fila operacional da Recepção/Médico funciona separadamente. Falta o elo entre esses dois fluxos: uma Consulta agendada precisa poder representar a chegada real do paciente, entrar na fila correta, iniciar quando o Médico chama e concluir junto com o atendimento operacional.

Esta change conecta Agenda e Fila sem criar prontuário, prescrição ou regras clínicas novas. A ideia é manter o fluxo simples: **Agendada → chegada confirmada → fila → atendimento → concluída**.

## What Changes

- Permitir que a Recepcionista execute a ação explícita **Confirmar chegada** em uma Consulta `AGENDADA`.
- No mesmo commit, a chegada:
  - altera a Consulta para `CONFIRMADA`;
  - registra `confirmed_at`;
  - cria exatamente uma entrada de fila `AGUARDANDO` vinculada à Consulta;
  - exige sintomas e prioridade informados manualmente pela Recepção, reutilizando as regras existentes da fila.
- Exigir que o profissional da Consulta esteja ativo e vinculado a uma conta com role Médico antes de confirmar a chegada.
- Vincular opcionalmente `QueueEntry` a uma Consulta por `consultation_id`, preservando entradas avulsas/walk-in sem Consulta.
- Garantir no banco que uma Consulta possua no máximo uma entrada de fila.
- Tornar entradas agendadas elegíveis somente ao Médico vinculado ao profissional da Consulta.
- Manter entradas avulsas elegíveis aos Médicos segundo o comportamento atual.
- Ao Médico chamar uma entrada agendada:
  - fila `AGUARDANDO → EM_ATENDIMENTO`;
  - Consulta `CONFIRMADA → EM_ANDAMENTO`;
  - registrar `started_at`;
  - tudo na mesma transação.
- Ao Médico finalizar uma entrada agendada:
  - fila `EM_ATENDIMENTO → FINALIZADO`;
  - Consulta `EM_ANDAMENTO → CONCLUIDA`;
  - registrar `completed_at`;
  - tudo na mesma transação.
- Ao Recepcionista retirar da fila uma entrada agendada ainda aguardando:
  - fila `AGUARDANDO → RETIRADO`;
  - Consulta `CONFIRMADA → CANCELADA`;
  - preservar motivo/timestamps;
  - liberar o slot somente quando ele continuar futuro/elegível, seguindo a mesma semântica de cancelamento existente.
- Manter reavaliação de sintomas/prioridade sem alterar o estado da Consulta.
- Atualizar a Agenda da Recepção para expor “Confirmar chegada” somente em Consulta `AGENDADA` e mostrar estados posteriores como informação operacional.
- Atualizar a Fila/Médico para sinalizar quando um atendimento veio de Consulta agendada.
- Manter RBAC server-side e locking PostgreSQL em todas as transições acopladas.

## Capabilities

### New Capabilities

- `consultation-care-lifecycle`: chegada da Consulta, vínculo com fila, elegibilidade por Médico e transições `CONFIRMADA → EM_ANDAMENTO → CONCLUIDA`, incluindo cancelamento operacional antes do início.

### Modified Capabilities

Nenhuma capability consolidada precisa ter requisitos substituídos. A nova capability especializa o conceito de “entrada elegível” já usado pela fila e consome os estados de Consulta já introduzidos por `appointment-scheduling`.

## Out of Scope

- confirmação automática por horário, SMS, e-mail ou WhatsApp;
- janela obrigatória de antecedência/atraso para chegada;
- check-in por paciente/totem;
- prontuário, anamnese, diagnóstico, prescrição ou exames;
- assinatura ZapSign;
- pagamento/Asaas;
- múltiplos profissionais no mesmo atendimento;
- redistribuição manual de Consulta confirmada para outro Médico;
- trocar profissional depois de `CONFIRMADA`;
- reabrir Consulta `CONCLUIDA`;
- cancelar Consulta em `EM_ANDAMENTO`;
- transformar automaticamente toda Consulta do dia em fila;
- alterar automaticamente prioridade clínica;
- remover o fluxo avulso/walk-in existente.

## Impact

- Adiciona timestamps de lifecycle à Consulta.
- Adiciona vínculo opcional e único de Consulta na fila.
- Introduz migration incremental sobre a revisão de appointment scheduling.
- Evolui serviços de fila para considerar elegibilidade de entradas agendadas por Médico.
- Evolui a Agenda da Recepção com confirmação de chegada.
- Evolui a tela do Médico com contexto de Consulta agendada sem criar prontuário.
- Exige testes concorrentes PostgreSQL para garantir que chegada/chamada/finalização não produzam estados divergentes.
- Mantém fila avulsa e agenda compatíveis com os dados já existentes.
