# Tarefas

## Etapa 1 — Visibilidade e navegação
- [x] Retirar links e rotas de Agenda e calendários dos papéis operacionais.
- [x] Substituir homepage de consultas do dia por fila real na Recepção.
- [x] Facilitar localização/cadastro e inclusão direta na fila.
- [x] Remover calendário do portal do paciente, sem inventar histórico inexistente.
- [ ] Validar screenshot real desktop/tablet/mobile das telas alteradas.

## Etapa 2 — Persistência clínica do episódio de fila (bloqueia o aceite funcional)
- [ ] Migration aditiva com vínculo obrigatório e exclusivo a Consulta legado OU QueueEntry.
- [ ] Criar registro clínico no claim de walk-in, sob lock/transação e controle de duplicidade.
- [ ] Autorização por Médico/episódio em leitura, escrita e impressão.
- [ ] Prescrições sem Consulta agendada; impressão usa data e autor do atendimento real.
- [ ] Histórico clínico paginado para atendimentos concluídos, incluindo legado.
- [ ] Portal do paciente read-only por identidade vinculada à fila.
- [ ] Foco/dirty state: não finalizar com alterações não salvas; nenhuma perda silenciosa.
- [ ] Remover caminhos ativos dependentes de agendamento e reconciliar contratos normativos.

## Etapa 3 — QA e integração
- [ ] Teste PostgreSQL de fila → chamada → prontuário → prescrição → finalização.
- [ ] Testes negativos: outras roles, outro Médico, outra conta Paciente, atendimento finalizado, chamadas concorrentes.
- [ ] Validar migração em PostgreSQL descartável, inclusive legado.
- [ ] Atualizar QA Chromium e matriz screenshots da PR #315 sem agenda e com estados de fila.
- [ ] Validar `reflex compile --dry`, pytest, OpenSpec e screenshots.
- [ ] Atualizar README, UX-CONTRACT, specs canônicas ao concluir o ciclo e revisar merge.

**Não declarar a migração concluída apenas porque a interface não mostra mais Agenda.**
