# Change: Gerenciamento operacional dos horários médicos

## Por quê

A agenda administrativa já apresenta calendário (PR #325), mas ainda mantém seletores de médico separados, abre pelo formulário de expediente e desabilita dias sem disponibilidade. A desativação não exige confirmação, e os horários do dia permanecem visualmente repetitivos.

## Objetivo

Tornar a visão mensal de disponibilidade a entrada principal de `/admin/horarios`, com contexto de médico único, consulta de dias vazios, contagens reais, operações administrativas seguras e formulários compactos.

## Escopo

- Unificar o médico selecionado entre calendário, expediente e horário avulso.
- Consultar qualquer dia pertencente ao mês exibido, inclusive dias sem slots.
- Exibir contagens de disponibilidade do dia com dados persistidos.
- Confirmar a desativação de horário disponível e impedir ações diretas em horários reservados.
- Reaproveitar os serviços de agenda, regras semanais e o design system existente.
- Testes de regressão para nomes legíveis e construção de calendário.

## Fora do escopo

- Alterar modelagem dos horários, duração ou janela móvel de 45 dias.
- Múltiplas regras semanais por médico ou seleção descontínua de dias.
- Operações em lote, cancelamento de consultas ou alterações de RBAC.
- APIs REST paralelas, novas dependências ou migrations.

## Riscos e verificação

O contrato existente de `ProfessionalWeeklySchedule` representa um intervalo contínuo de dias. Slots `BOOKED` são protegidos no serviço server-side. Validar com OpenSpec strict, Pytest, Reflex compile e Chromium antes de integração.
