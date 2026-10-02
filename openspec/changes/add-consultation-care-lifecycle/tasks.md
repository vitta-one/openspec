## 1. Domínio e persistência

- [x] 1.1 Adicionar `confirmed_at`, `started_at` e `completed_at` nullable à Consulta.
- [x] 1.2 Adicionar `consultation_id` nullable à QueueEntry com FK `RESTRICT`.
- [x] 1.3 Garantir persistência de no máximo uma QueueEntry por Consulta.
- [x] 1.4 Preservar QueueEntries existentes como walk-in com `consultation_id = NULL`.
- [x] 1.5 Gerar migration incremental sobre `9f7c2a1b4d6e` com upgrade/downgrade revisados.
- [x] 1.6 Registrar índices necessários para lookup de fila por Consulta e elegibilidade.
- [x] 1.7 Validar migration em PostgreSQL 16 descartável.

## 2. Serviço de lifecycle da Consulta

- [x] 2.1 Criar módulo de serviço para transições entre Consulta e fila sem depender do State/UI.
- [x] 2.2 Implementar validação fechada de `AGENDADA → CONFIRMADA`.
- [x] 2.3 Validar profissional ativo antes da confirmação de chegada.
- [x] 2.4 Validar que o profissional possui `user_id` ligado a conta com role `MEDICO`.
- [x] 2.5 Validar sintomas e prioridade recebidos sem inferência clínica.
- [x] 2.6 Bloquear Consulta com `FOR UPDATE` durante confirmação.
- [x] 2.7 Criar QueueEntry `AGUARDANDO` e atualizar Consulta no mesmo commit.
- [x] 2.8 Converter conflito concorrente/unique em erro de negócio seguro.
- [x] 2.9 Preservar `confirmed_at` original em tentativas repetidas.
- [x] 2.10 Implementar helper transacional de `CONFIRMADA → EM_ANDAMENTO`.
- [x] 2.11 Implementar helper transacional de `EM_ANDAMENTO → CONCLUIDA`.
- [x] 2.12 Implementar helper transacional de `CONFIRMADA → CANCELADA` por retirada da fila.
- [x] 2.13 Reutilizar a regra de liberação/inativação do slot no cancelamento operacional.
- [x] 2.14 Garantir que reavaliação não altere estado/timestamps da Consulta.

## 3. Elegibilidade e locking da fila Médica

- [x] 3.1 Definir walk-in como QueueEntry sem Consulta vinculada.
- [x] 3.2 Alterar contagem do Médico para incluir walk-ins + Consultas vinculadas ao próprio profissional.
- [x] 3.3 Excluir da contagem do Médico Consultas pertencentes a outro profissional.
- [x] 3.4 Alterar seleção do próximo paciente preservando prioridade → entrada → id.
- [x] 3.5 Aplicar elegibilidade por `EXISTS`/subquery sem lock de outer join opcional.
- [x] 3.6 Manter `FOR UPDATE SKIP LOCKED` sobre QueueEntry elegível.
- [x] 3.7 Ao chamar QueueEntry agendada, bloquear/revalidar Consulta antes de persistir.
- [x] 3.8 Rejeitar chamada quando Consulta não estiver `CONFIRMADA`.
- [x] 3.9 Associar `doctor_user_id` e transicionar Consulta para `EM_ANDAMENTO` no mesmo commit.
- [x] 3.10 Ao finalizar, exigir ownership atual da QueueEntry e Consulta `EM_ANDAMENTO`.
- [x] 3.11 Finalizar QueueEntry + Consulta no mesmo commit.
- [x] 3.12 Preservar comportamento atual de claim/finalize para walk-ins.

## 4. Recepção e retirada

- [x] 4.1 Criar operação Recepcionista `confirm_arrival` com RBAC server-side.
- [x] 4.2 Reutilizar o paciente já associado à Consulta; não permitir troca na chegada.
- [x] 4.3 Rejeitar confirmação quando profissional não estiver apto.
- [x] 4.4 Integrar retirada de QueueEntry agendada à transição `CONFIRMADA → CANCELADA`.
- [x] 4.5 Usar o mesmo timestamp para `withdrawn_at` e `cancelled_at`.
- [x] 4.6 Preservar motivo de retirada e histórico da Consulta.
- [x] 4.7 Manter retirada walk-in sem efeito em Consulta.
- [x] 4.8 Manter reavaliação de fila agendada independente do lifecycle da Consulta.
- [x] 4.9 Garantir que handlers antigos de reagendamento/cancelamento continuem rejeitando estados posteriores a `AGENDADA`.

## 5. State e UI da Recepção

- [x] 5.1 Estender `ReceptionAgendaState` com diálogo de confirmação de chegada.
- [x] 5.2 Exibir paciente, profissional e horário da Consulta como contexto somente leitura no diálogo.
- [x] 5.3 Adicionar campos de sintomas e prioridade com labels reais e validação do app.
- [x] 5.4 Renderizar “Confirmar chegada” somente para Consulta `AGENDADA`.
- [x] 5.5 Após sucesso, atualizar Agenda e fila sem exigir reload completo da página.
- [x] 5.6 Em conflito/erro corrigível, manter diálogo e valores necessários para correção.
- [x] 5.7 Para `CONFIRMADA`, exibir estado operacional indicando que o paciente já está na fila.
- [x] 5.8 Para `EM_ANDAMENTO`, `CONCLUIDA` e `CANCELADA`, manter ações incompatíveis indisponíveis.
- [x] 5.9 Sinalizar em QueueEntry quando a origem for Consulta agendada.
- [x] 5.10 Manter fluxo responsivo em uma coluna e sem rolagem horizontal obrigatória.

## 6. State e UI do Médico

- [x] 6.1 Ajustar `DoctorQueueState` para contagem elegível por Médico autenticado.
- [x] 6.2 Preservar estado vazio quando não houver walk-in nem Consulta própria aguardando.
- [x] 6.3 Exibir no atendimento ativo se a QueueEntry deriva de Consulta agendada.
- [x] 6.4 Exibir horário/profissional já persistidos quando aplicável, sem criar prontuário.
- [x] 6.5 Atualizar cópia da fila para explicar que Consultas agendadas respeitam o profissional marcado.
- [x] 6.6 Preservar foco, teclado, reduced-motion e layout estreito.

## 7. Preview local e documentação

- [x] 7.1 Fazer o preview local do Administrador refletir os novos estados/timestamps sem permitir mutações de Recepção/Médico.
- [x] 7.2 Atualizar `UX-CONTRACT.md` com semântica de “Confirmar chegada” e bridge Agenda→Fila.
- [x] 7.3 Atualizar `DESIGN.md` somente se necessário para registrar padrão durável de lifecycle.
- [x] 7.4 Atualizar README com o novo fluxo operacional sem apresentar prontuário como implementado.
- [x] 7.5 Manter estados textuais como fonte primária; cor permanece secundária.

## 8. Testes e validação

- [x] 8.1 Testar confirmação de chegada válida e criação atômica de QueueEntry.
- [x] 8.2 Testar sintomas/prioridade inválidos sem alteração de Consulta.
- [x] 8.3 Testar profissional inativo e profissional sem conta Médica.
- [x] 8.4 Testar duas confirmações concorrentes produzindo no máximo uma QueueEntry.
- [x] 8.5 Testar que walk-in continua elegível sem Consulta.
- [x] 8.6 Testar que Médico não vê/chama Consulta de outro profissional.
- [x] 8.7 Testar que Médico correto chama e transiciona Consulta para `EM_ANDAMENTO` atomicamente.
- [x] 8.8 Testar chamada concorrente sem duplicar ownership nem divergir estado.
- [x] 8.9 Testar finalização válida `EM_ANDAMENTO → CONCLUIDA`.
- [x] 8.10 Testar finalização por Médico diferente e estado inconsistente.
- [x] 8.11 Testar retirada agendada `CONFIRMADA → CANCELADA` e regra do slot.
- [x] 8.12 Testar retirada walk-in sem alteração de Consulta.
- [x] 8.13 Testar reavaliação preservando Consulta `CONFIRMADA`.
- [x] 8.14 Testar RBAC e sessões ausente/expirada nas novas operações.
- [x] 8.15 Validar locking/constraints em PostgreSQL 16 real do CI.
- [ ] 8.16 Executar OpenSpec strict, migration, suíte completa e `reflex compile --dry`, corrigindo regressões antes de concluir.
