## Implementação

- [x] Inspecionar o fluxo de reserva, RBAC, Agenda, dashboard, disponibilidade e PR #325 já mesclada.
- [x] Criar seleção de paciente existente e médico ativo com especialidade opcional.
- [x] Implementar cinco etapas e calendário real no modal compartilhado, responsivo.
- [x] Manter única reserva via `reception_schedule_consultation` e atualizar visões após persistência.
- [x] Preservar rota legada como alias e entrada a partir da ficha do paciente.
- [x] Evitar mensagem de falha quando reserva concluiu e só o refresh falhou.
- [x] Adicionar regressões unitárias para disponibilidade, máscara e RBAC.

## QA

- [ ] Validar OpenSpec em modo strict na CI.
- [ ] Executar suíte Pytest, inclusive testes PostgreSQL de concorrência.
- [ ] Executar `reflex compile --dry`.
- [ ] Homologar teclado/Escape/foco e viewports 320/390/768/1024/1440 no Chromium.
- [ ] Validar ausência de regressão no portal de autoagendamento.
- [ ] Revisar e arquivar change somente após merge e evidências aprovadas.

## Riscos conhecidos

A revisão manual de fluxo e acessibilidade ainda é necessária; sem evidência, não marcar QA como aprovado.
