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
- [ ] 3.5 Revisar diff integrado e estado do CI, criar commits convencionais, publicar a branch e atualizar a PR para `develop`; verificar URL, alvo e ausência de merge/deploy.

## Registro da rodada de validação — 2026-11-20 a 2026-11-21

- Chromium com o bundle do HEAD: 96/96 capturas concluídas em QA14 nas seis resoluções; 16/16 comparações desktop geradas e reinspecionadas sem máscaras. O runner remove foco transitório e volta ao topo após interações para manter o frame canônico.
- Geometria do Financeiro registrada pelo DOM em 1768×890 e composição final ajustada ao viewport de referência; detalhes e medidas por rota estão em `docs/qa/operational-screen-parity-2026-11-17.md`.
- Pytest em PostgreSQL 16.16 `vitta_one_test`: 572 aprovados, 3 skips explicados no relatório. Chromium funcional/acessibilidade: 42 aprovados em QA14; reflow 2×: 16/16 na rodada de layout anterior.
- Corrigida a corrida da busca vazia da Recepção removendo a atualização controlada por caractere: o formulário envia o valor nativo (incluindo vazio), a ação limpar zera o campo no DOM e o State, e reloads antigos são descartados. O browser confirmou o retorno de `8 de 8` para `8 de 24` após limpar a busca por profissional.
- Validação OpenSpec strict: 34 aprovados, zero falhas. A aprovação visual integral permanece em 0/16: diferenças de arte e de conteúdo/fixtures estão documentadas e não foram mascaradas ou substituídas por dados clínicos fictícios.
- A correção final passou localmente: 572 testes Python, 42 testes Chromium e 96/96 capturas; compile Reflex e validação OpenSpec estão atualizados no relatório. Publicação e CI pós-push ainda pendentes.
- PR [#358](https://github.com/vitta-one/openspec/pull/358) permanece aberta para `develop`. O SHA remoto anterior `b16c372f915f004e76f4f39260e01feedc49e5f1` passou Validate Vitta-One e Vitta One | CI Produção; o Chromium identificou a corrida de busca descrita acima. A correção final foi validada localmente e será publicada nesta rodada.
- Nenhum merge, deploy, migration de produção ou alteração de banco de produção foi feito.
