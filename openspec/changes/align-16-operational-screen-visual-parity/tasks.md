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

## 3. Evidência visual e regressão

- [x] 3.1 Implementar runner isolado para as 16 rotas × seis viewports; verificar 96 capturas novas e manifesto com viewport, rota, estado e resultado.
- [x] 3.2 Gerar lado a lado, overlay e diff para cada uma das 16 referências desktop sem deformar imagens; inspecionar visualmente todas as rotas e separar diferenças de dados de layout.
- [x] 3.3 Atualizar o relatório `docs/qa/operational-screen-parity-2026-11-17.md` com matriz individual de 16 rotas, medidas, resultados, dados, acessibilidade, responsividade e discrepâncias residuais.
- [x] 3.4 Executar regressão: `pytest -q`, `reflex compile --dry`, capturas/comparações, `git diff --check` e OpenSpec strict; registrar comandos e status reais.
- [x] 3.5 Revisar diff integrado e estado do CI, criar commits convencionais, publicar a branch e abrir uma única PR para `develop`; verificar URL, alvo e ausência de merge/deploy.
