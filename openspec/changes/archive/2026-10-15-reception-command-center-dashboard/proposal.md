## Why

O dashboard já apresenta métricas reais, mas a hierarquia deixa duas métricas no rodapé, não lista as consultas que exigem revisão e mostra zeros antes da primeira leitura. As contagens também usam dez consultas SQL sequenciais. A Recepção precisa identificar a próxima ação sem receber números simulados ou novas regras clínicas.

## What Changes

- Consolidar contagens de consultas e fila em duas projeções SQL.
- Apresentar seis KPIs rastreáveis e acessos às rotas já existentes.
- Enriquecer próximas consultas com situação operacional e link para a Agenda.
- Listar até cinco pendências de chegada, com total e link para revisão.
- Diferenciar carregamento inicial, dados carregados, atualização e falha.
- Melhorar quebra de linha e foco visível nos cards de KPI.
- Registrar a auditoria da Recepção e sincronizar contrato UX/specs.

## Capabilities

- MODIFIED: `reception-operational-dashboard`.

## Fora de escopo

Tempo de espera, inferência de ausência/no-show, urgência médica, confirmação de chegada no dashboard, conexão em tempo real, polling, novas rotas, mudanças em Agenda/Pacientes/Fila, migrações, novos modelos, dados ou campos clínicos.
