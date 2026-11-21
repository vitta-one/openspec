## 1. Baseline e contrato visual

- [x] 1.1 Registrar para cada PNG dimensões, rota e marcos geométricos e confirmar visualmente as 16 referências e capturas baseline; verificar os registros no relatório de QA.
- [x] 1.2 Confirmar shell, tokens e estado atual de cada rota no código e estabelecer uma fixture PostgreSQL local descartável; verificar URL/porta segura e dados sintéticos antes de iniciar a aplicação.

## 2. Shell e páginas

- [x] 2.1 Corrigir a geometria compartilhada de sidebar, topbar e conteúdo sem perder variantes por role ou estado manual; verificar rotas das quatro roles em desktop e drawer mobile.
- [x] 2.2 Ajustar composição, densidade e alinhamento das telas de Recepção e comparar suas capturas novas com as referências 01–05.
- [x] 2.3 Ajustar composição, densidade e alinhamento das telas administrativas e financeira e comparar suas capturas novas com as referências 06–12.
- [x] 2.4 Ajustar composição, densidade e alinhamento das telas médicas e comparar suas capturas novas com as referências 13–16.
- [x] 2.5 Revisar teclado, foco, nomes acessíveis, estados de loading/vazio/erro, zoom e seis viewports nas telas afetadas; registrar verificações e limitações.
- [x] 2.6 Garantir que cada link da lista de pacientes derive a ficha do ID da mesma linha e validar no Chromium que destino e identidade exibida correspondem ao paciente selecionado.
- [x] 2.7 Substituir gaps numéricos inválidos nas grades Reflex por unidades CSS explícitas e alinhar sidebar e formulário de pacientes às medidas dos PNGs; confirmar nas capturas DOM finais.

## 3. Evidência visual e regressão

- [x] 3.1 Implementar runner isolado para as 16 rotas × seis viewports; verificar 96 capturas novas e manifesto com viewport, rota, estado e resultado.
- [x] 3.2 Gerar lado a lado, overlay e diff para cada uma das 16 referências desktop sem deformar imagens; inspecionar visualmente todas as rotas e separar diferenças de dados de layout.
- [x] 3.3 Atualizar o relatório `docs/qa/operational-screen-parity-2026-11-17.md` com matriz individual de 16 rotas, medidas, resultados, dados, acessibilidade, responsividade e discrepâncias residuais.
- [x] 3.4 Executar regressão: `pytest -q`, `reflex compile --dry`, capturas/comparações, `git diff --check` e OpenSpec strict; registrar comandos e status reais.
- [x] 3.5 Revisar diff integrado e estado do CI, criar commits convencionais, publicar a branch e atualizar a PR para `develop`; verificar URL, alvo e ausência de merge/deploy.

## Registro da rodada de validação — 2026-11-20 a 2026-11-21

- Chromium com o bundle do HEAD: 96/96 capturas concluídas em QA14 nas seis resoluções; 16/16 comparações desktop geradas e reinspecionadas sem máscaras. O runner remove foco transitório e volta ao topo após interações para manter o frame canônico.
- Geometria do Financeiro registrada pelo DOM em 1768×890 e composição final ajustada ao viewport de referência; detalhes e medidas por rota estão em `docs/qa/operational-screen-parity-2026-11-17.md`.
- Pytest em PostgreSQL 16.16 `vitta_one_test`: 572 aprovados, 3 skips explicados no relatório. Chromium funcional/acessibilidade: 42 aprovados em QA14; reflow 2×: 16/16 na rodada de layout anterior.
- Corrigida a corrida da busca vazia da Recepção removendo a atualização controlada por caractere: o formulário envia o valor nativo (incluindo vazio), a ação limpar zera o campo no DOM e o State, e reloads antigos são descartados. O browser confirmou o retorno de `8 de 8` para `8 de 24` após limpar a busca por profissional.
- Validação OpenSpec strict: 34 aprovados, zero falhas. A aprovação visual integral permanece em 0/16: diferenças de arte e de conteúdo/fixtures estão documentadas e não foram mascaradas ou substituídas por dados clínicos fictícios.
- A correção final passou localmente: 572 testes Python, 42 testes Chromium e 96/96 capturas; compilação Reflex, migrations e validação OpenSpec estão atualizadas no relatório.
- Commits publicados: `b9fa2d4` (busca diária), `982eba1` (captura visual) e `2ee8579` (relatório de QA). CI pós-push passou 3/3 no SHA `2ee85798be7b5022f756e47438c1bb75303181c7`, incluindo 37 testes gerais, 5 de agenda, 93/93 capturas gerais e 96/96 capturas operacionais; artifact está no relatório.
- PR [#358](https://github.com/vitta-one/openspec/pull/358) permanece aberta para `develop`. O campo de busca e o Chromium passaram na regressão final; nenhum merge foi feito.
- Nenhum merge, deploy, migration de produção ou alteração de banco de produção foi feito.

## Registro de revisão adicional — 21/11/2026

- Reaberta a referência 04 após apontamento da usuária; o overlay local sem máscaras evidenciou ícones menores/deslocados e a faixa de ações 3 px abaixo do PNG.
- Ajustados os ícones e alinhamentos medidos da tela de cadastro e o placeholder para caber em 320 px; o runner verifica a largura no viewport estreito.
- Regeneradas as 96 capturas e os 16 comparativos depois do build Reflex atual. As diferenças da tela 04 caíram de 13,09% para 7,56% no limiar RGB L1≥36 (MAE/canal de 13,32 para 8,59).
- Todos os quatro comparativos agregados foram reinspecionados; a paridade integral permanece não comprovada (**0/16 aprovações**). Diferenças de dados, estados, ícones e rasterização continuam abertas no relatório de QA; nenhuma captura foi mascarada.
- Nenhum dado clínico ou financeiro foi alterado para aproximar os PNGs.

## Registro de continuação — 21/11/2026

- Build Reflex `--env prod` executado com o código corrente da branch e PostgreSQL 16 QA isolado/migrado até `f031a5aa5002 (head)`; smoke HTTP 200 confirmado após redirecionamento.
- Regeneradas 96/96 capturas nas seis resoluções com fixture sintética limpa e as 16 referências originais locais. Foram gerados 16 comparativos sem máscaras (lado a lado, overlay de 50% e diff amplificado) e quatro folhas de revisão; todos foram inspecionados novamente. `fidelity-assessment.json` permanece `REVIEW_REQUIRED`, com **0/16 aprovadas integralmente** e faixa de diferença RGB L1≥36 de 4,14%–16,07%.
- Os resíduos de dados/estado foram detalhados por rota no relatório de QA. Não se criaram cobranças ou registros clínicos falsos para aproximar a imagem; a concentração de consultas de QA no sábado é efeito da fixture usada para a tabela diária.
- Corrigida a corrida de criação de cobrança: após resolver o cliente e readquirir o lock da consulta, o serviço revalida a cobrança ativa antes de inserir; índice único permanece como proteção final. O teste determinístico é verde em SQLite e PostgreSQL e prova que não há segundo INSERT nem chamada externa.
- Ajustado o teste Chromium do autogendamento para navegar para a semana do horário escolhido, cobrindo a virada de semana sem depender do dia atual.
- Validações: Pytest **574 passed, 3 skipped**; Chromium **42 passed**; OpenSpec strict **34 passed, 0 failed**; `compileall`, `reflex compile --dry`, migrations/head e `git diff --check` aprovados. Avisos de depreciação Reflex/Starlette e a nota OpenSpec estão descritos no relatório.
- Aprovação visual permanece **0/16**; diferenças de conteúdos, estados e rasterização continuam mensuradas e documentadas, sem declaração de pixel-idêntica.

## Recaptura local com guard de QA endurecido — 2026-11-21

- [x] Recriar o PostgreSQL 16 descartável `vitta_one_operational_ui_qa_22`, executar Alembic até `f031a5aa5002 (head)`, semear apenas identidades/dados sintéticos e iniciar o bundle atual da branch nesse banco.
- [x] Regenerar a matriz das 16 rotas em seis viewports: **96/96 PASS**, zero falhas, zero imagens quebradas, zero overflow horizontal. Gerar comparativos desktop sem máscaras e reinspecionar os quatro painéis agregados.
- [x] Recalcular métricas sem esconder divergências: RGB L1≥36 de **4,14% a 16,06%**, média **9,49%**; MAE médio **9,21**. Resultado honesto: **0/16 aprovações integrais**, estado `REVIEW_REQUIRED`.
- [x] Endurecer o guard para rejeitar o nome genérico `vitta_one` na porta local 15433 e cobrir o caso com teste: **3/3** testes direcionados aprovados.
- [x] Atualizar `docs/qa/operational-screen-parity-2026-11-17.md` com o resultado QA22, a tabela por tela e a comparação temporária de fonte, sem modificar fonte global porque a diferença medida foi marginal e inconsistente.
- [x] Repetir Pytest completo em PostgreSQL descartável novo `vitta_one_test_22`: **574 passed, 3 skipped**; Chromium contra o build recém-iniciado com QA22: **42 passed** em 173,81 s. `reflex compile --dry`, `compileall`, OpenSpec strict e `git diff --check` passaram nesta revisão.
- Nenhum dado de paciente, consulta, fila, vínculo médico, prontuário, exame ou cobrança foi alterado para reduzir a diferença. As diferenças visuais permanecem em aberto; esta tarefa não marca fidelidade integral como concluída.

## Revalidação da largura mínima e captura determinística — 2026-11-21

- [x] Corrigir o placeholder do nome que a CI Chromium Ubuntu cortou em 320 px e confirmar a largura do texto contra a área útil do input.
- [x] Esperar `document.fonts.ready` antes dos screenshots e confirmar duas capturas byte a byte idênticas no mesmo Chromium/contexto.
- [x] Recriar captura limpa QA23 e regenerar/inspecionar comparativos: **96/96**; RGB L1≥36 médio **9,51%**, MAE/canal médio **9,26**.
- [x] Repetir Pytest PostgreSQL descartável: **574 passed, 3 skipped**; Chromium funcional/acessibilidade/responsividade: **42 passed**; OpenSpec strict **34/34**, `compileall`, `reflex compile --dry` e `git diff --check` aprovados.
- [ ] Resolver as diferenças visuais restantes de cada rota e obter inspeção humana de paridade integral. A classificação atual é **0/16 aprovações**, `REVIEW_REQUIRED`; não substituir divergências clínicas/financeiras por registros fictícios.
