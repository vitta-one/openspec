## 1. Especificação e desenho

- [x] 1.1 Documentar o calendário de sete dias, seleção, situação, timezone e limites de duração/disponibilidade no delta OpenSpec.
- [x] 1.2 Atualizar a spec consolidada e o UX-CONTRACT conforme o comportamento implementado.
- [x] 1.3 Revisar hierarquia de tarefas da Recepção, estados vazios, conteúdo sensível e foco por teclado.

## 2. Dados e State

- [x] 2.1 Trocar a lista de próximas consultas por uma projeção cronológica dos compromissos persistidos dos próximos sete dias locais.
- [x] 2.2 Manter status textuais, cancelamentos identificados, métrica ativa sem canceladas e pendência somente pela regra existente.
- [x] 2.3 Preservar a autorização server-side e o limite de quatro consultas SQL.
- [x] 2.4 Testar início/fim do período local, estados cancelados e ordenação.

## 3. Interface

- [x] 3.1 Exibir os sete dias como calendário visual e selecionar o conteúdo de um dia com controles acessíveis.
- [x] 3.2 Melhorar padding interno e ritmo vertical dos painéis, métricas e linhas sem alterar o design system de outros módulos.
- [x] 3.3 Manter ações reais, links para os módulos protegidos e estados de carregamento, falha e dia sem consultas.
- [x] 3.4 Validar seleção por teclado e viewports de 320, 375 e 768 px sem overflow.

## 4. Verificação e entrega

- [x] 4.1 Executar testes relevantes, reflex compile --dry e validação OpenSpec.
- [x] 4.2 Executar QA Chromium, inspecionar screenshots do dashboard e corrigir diferenças de espaçamento/legibilidade encontradas.
- [x] 4.3 Registrar evidências de CI e abrir PR para develop; não fazer merge.


## Evidências de verificação

- CI Validate Vitta-One: OpenSpec 9 aprovados, migração PostgreSQL descartável, 187 testes aprovados (1 aviso SQLAlchemy pré-existente) e `reflex compile --dry` aprovado ([run #242](https://github.com/vitta-one/openspec/actions/runs/38664776748)).
- QA Chromium: 19 testes aprovados, incluindo teclado e responsividade; capturas do dashboard em 320, 375 e 768 px foram inspecionadas ([run #74](https://github.com/vitta-one/openspec/actions/runs/38664776741)).
- Auditor estrito frontend-design-premium: 0 achados; detector Impeccable de layout: 0 achados.
