# Relatório de paridade visual das telas operacionais — 20–21/11/2026

## Escopo e método

Continuação do checkpoint `bfe77d9001a875574f39b8aafb89859d4ad5beff` na branch `fix/visual-parity-16-screens-20261117`. A implementação permaneceu em Reflex, preservando States, handlers server-side, modelos, serviços e autorização existente.

As 16 referências PNG anexadas foram conferidas por SHA-256 contra o anexo com o mesmo número/nome e abertas/decodificadas novamente no fim da rodada. A referência 01 mede 1774×887; ela foi ajustada proporcionalmente com `contain` ao quadro 1768×890, com faixa de 3 px no eixo Y. As outras 15 já medem 1768×890. Não foram aplicadas máscaras. A matriz visual final foi refeita em 20/11 no PostgreSQL descartável QA14, com o bundle atualizado e uma fixture recém-semeada. A regressão interativa foi repetida em seguida no mesmo banco; as capturas canônicas foram feitas antes de testes que alteram registros sintéticos.

O runner `qa_browser.capture_operational_reference_screens` registrou dimensões e caixas via `getBoundingClientRect()`, estilos computados, imagens carregadas, URL, títulos e overflow. Foram gerados PNGs, lado a lado, overlays a 50%, diffs amplificados e quatro folhas de comparação em `qa-artifacts/operational-reference/` (ignorado pelo Git). As quatro folhas com as 16 telas foram inspecionadas visualmente após a captura final. Métricas de pixels são diagnósticas e contam também conteúdo, texto, dados e variações de rasterização; não representam uma nota de fidelidade.

## Status de evidência

| Evidência | Resultado |
|---|---|
| Capturas concluídas | **96/96 PASS**, 16 rotas × seis viewports; sem falhas de navegação ou overflow horizontal global |
| Carregamento das imagens | **96/96** capturas sem imagens quebradas; todas completas e com `naturalWidth > 0` |
| Smoke de rota e controles | **16/16 PASS** no navegador, com agenda, paginação de recepção e filtros de especialidades incluídos |
| Comparações geradas | **16/16** com referência alinhada, lado a lado, overlay e diff; sem máscaras |
| Comparações inspecionadas | **16/16**, após as últimas correções de layout e Financeiro |
| Aprovação visual integral | **0/16**; todas as 16 foram inspecionadas, mas ainda têm diferenças residuais de conteúdo, arte ou composição descritas abaixo |
| Aprovação como pixel-idêntica | **0/16**; não se declara identidade visual sem comprovação |
| Reflow equivalente a 200% | **16/16 PASS** em viewport CSS 884×445, sem overflow ou imagens quebradas |

Os comparativos individuais e manifestos detalhados permanecem em `qa-artifacts/operational-reference/`: folhas `comparativo-01-04.png`, `comparativo-05-08.png`, `comparativo-09-12.png` e `comparativo-13-16.png`; cada rota também tem `side-by-side.png`, `overlay-50.png` e `diff-amplified-3x.png`. As quatro folhas da captura QA14 foram abertas e inspecionadas; elas mostram a composição do bundle atual, variantes de grid/sidebar e Financeiro. Após os testes de interação de cada rota, o runner desfoca o controle e volta ao topo antes de capturar para não registrar rolagem provocada por validações. A escala de 200% foi verificada como viewport CSS reduzido à metade, não por alteração do zoom do sistema operacional.

## Avaliação por tela

| # / rota | Captura e navegação | Inspeção visual e diferenças residuais |
|---|---|---|
| 01 `/recepcao` | 6/6; rota PASS | A grade de KPIs, a tabela e as duas colunas laterais correspondem à hierarquia da referência. A barra agora oferece busca por paciente, profissional e horário e filtro de situação, com consulta server-side. Contagens, nomes e estados da fixture continuam diferentes; os painéis inferiores permanecem dentro da primeira dobra. Diferença de pixels acima do limiar RGB L1=36: 16.06%; MAE RGB por canal: 13.54. |
| 02 `/recepcao/agenda` | 6/6; rota PASS | A semana em grade é o componente central e os controles de navegação funcionam. A distribuição das consultas na semana sintética não corresponde aos dias e nomes mostrados no PNG; a agenda vazia do médico de QA permanece sem linhas. Diferença de pixels acima do limiar RGB L1=36: 13.22%; MAE RGB por canal: 10.32. |
| 03 `/recepcao/pacientes` | 6/6; rota PASS | Busca, tabela e paginação são reais e a composição corresponde à lista da referência. A fixture tem mais pacientes e linhas; o cabeçalho usa o SVG próprio disponível, diferente da ilustração raster original. Diferença de pixels acima do limiar RGB L1=36: 11.09%; MAE RGB por canal: 12.63. |
| 04 `/recepcao/pacientes/novo` | 6/6; rota PASS | Formulário compacto e painel de orientações lado a lado, com campos/validações existentes. A ilustração e o texto orientativo são ativos do projeto e diferem da referência. Diferença de pixels acima do limiar RGB L1=36: 12.83%; MAE RGB por canal: 13.14. |
| 05 `/recepcao/fila` | 6/6; rota PASS | Cabeçalho ilustrado, ação principal, métricas horizontais e painel da fila seguem a composição aprovada. A fixture persistida contém uma entrada sintética aguardando, enquanto o PNG mostra o estado vazio; a linha não foi removida nem mascarada. Diferença de pixels acima do limiar RGB L1=36: 11.94%; MAE RGB por canal: 12.05. |
| 06 `/admin` | 6/6; rota PASS | Métricas, dois grupos operacionais e atalhos mantêm a organização da referência. Contagens e especialidades vêm da fixture e divergem (13 especialidades contra 6 no PNG); a arte vetorial própria também difere. Diferença de pixels acima do limiar RGB L1=36: 13.72%; MAE RGB por canal: 10.33. |
| 07 `/admin/funcionarios` | 6/6; rota PASS | Indicadores, busca/filtros, tabela e paginação estão alinhados. A quantidade e os dados sintéticos de funcionários diferem do mockup; o seletor de tamanho da página e a quebra em 320 px foram validados. Diferença de pixels acima do limiar RGB L1=36: 9.64%; MAE RGB por canal: 8.70. |
| 08 `/admin/funcionarios/novo` | 6/6; rota PASS | Formulário e banner preservam a distribuição da referência. O formulário inicia vazio por usar o fluxo real de cadastro; o banner é a arte SVG existente, não o ativo original. Diferença de pixels acima do limiar RGB L1=36: 8.66%; MAE RGB por canal: 8.67. |
| 09 `/admin/especialidades` | 6/6; rota PASS | Indicadores, filtros horizontais, tabela e paginação correspondem à composição. Busca e situação medem Y=369,75 px, altura 40 px, desvio vertical 0 px. A fixture tem 13 especialidades contra 6 na referência. Diferença de pixels acima do limiar RGB L1=36: 11.34%; MAE RGB por canal: 11.06. |
| 10 `/admin/horarios` | 6/6; rota PASS | A seleção de profissional e o estado vazio ocupam as mesmas áreas principais do PNG. Sem profissional selecionado, os horários não são inventados; a ilustração é um SVG próprio. Diferença de pixels acima do limiar RGB L1=36: 7.84%; MAE RGB por canal: 7.37. |
| 11 `/admin/configuracoes` | 6/6; rota PASS | Formulário compacto e painel auxiliar lado a lado. O banco descartável não tem configuração clínica persistida, então os campos permanecem vazios em vez de copiar valores do PNG; sem dados clínicos fictícios. Diferença de pixels acima do limiar RGB L1=36: 10.79%; MAE RGB por canal: 11.01. |
| 12 `/financeiro` | 6/6; rota PASS | Indicadores, filtros, emissão, tabela e evolução foram recompostos com dados do serviço/State existentes. Medidas DOM finais em 1768×890: conteúdo x=169, largura=1554; indicadores y=167,4; filtros y=262,6; emissão y=411; cobranças y=563; evolução y=783. O cabeçalho da tabela mede 33,5 px. O PNG tem outras datas/valores/linhas e outro papel de sessão no topbar; nenhuma cobrança foi fabricada. A arte original não está no projeto. Diferença de pixels acima do limiar RGB L1=36: 10.29%; MAE RGB por canal: 10.00. |
| 13 `/medico` | 6/6; rota PASS | Sidebar médica expandida, métricas e painéis clínicos mantêm a hierarquia. A fila compartilhada de QA mostra uma entrada sintética enquanto o PNG está vazio; não há atendimento ativo para esta identidade. Não se criaram dados médicos para a captura. Diferença de pixels acima do limiar RGB L1=36: 14.23%; MAE RGB por canal: 11.88. |
| 14 `/medico/agenda` | 6/6; rota PASS | Cartões da semana e calendário mensal estão presentes; a agenda é filtrada pelo profissional associado no servidor. O profissional sintético de QA não tem consultas vinculadas, ao contrário das entradas do PNG. Diferença de pixels acima do limiar RGB L1=36: 12.12%; MAE RGB por canal: 10.52. |
| 15 `/medico/pacientes` | 6/6; rota PASS | Lista vinculada e estado vazio respeitam a projeção autorizada do médico. O médico QA não tem pacientes vinculados, enquanto o PNG contém registros; não foram fabricados vínculos clínicos. Diferença de pixels acima do limiar RGB L1=36: 12.21%; MAE RGB por canal: 10.02. |
| 16 `/medico/prontuarios` | 6/6; rota PASS | Painel do prontuário atual e estado vazio estão presentes. A identidade de QA não tem atendimento/prontuário ativo; não foram criados diagnósticos, exames ou prontuários sintéticos para imitar a imagem. Diferença de pixels acima do limiar RGB L1=36: 11.98%; MAE RGB por canal: 8.71. |

Cada percentual inclui rasterização, texto, dados, ícones e arte; não é um classificador de defeitos. As diferenças de dados não foram mascaradas. Os números acima vêm do manifesto da última captura, feita com banco QA14 recém-criado em 20/11/2026.

### Diferenças que permanecem

- As imagens ilustrativas são SVGs próprios existentes no projeto, não os ativos originais. Cinco referências quebradas para `/clinic-building-hero.svg` e `/clinic-building-guide.svg` foram corrigidas para o SVG existente `/clinic-operational-hero.svg`; a checagem de carregamento agora torna esse tipo de regressão explícito.
- Os dados de QA não são cópias dos valores dos PNGs. As diferenças de contagem, datas, registros, estado vazio e conteúdo estão discriminadas por rota acima e não foram ocultadas com máscaras.
- Os estados de cobrança real, envio Resend e webhook público não foram homologados: não há credenciais sandbox/providers nem endpoint HTTPS público neste ambiente. Os testes correspondentes usam os mocks existentes.
- As comparações finais registram diferenças de pixels entre 7,84% e 16,06% no limiar RGB L1=36. Isso inclui conteúdo/data, texto, arte e renderização, não isola apenas geometria. Todas as 16 comparações foram inspecionadas; nenhuma recebeu aprovação visual integral ou identidade pixel a pixel, e os resíduos estão discriminados por rota.

## Correções aplicadas nesta continuação

- Corrigida a especificidade do seletor de pesquisa de especialidades; DOM final mede 40 px em ambos os campos e 0 px de desalinhamento vertical.
- Corrigido o valor do `Select` de tamanho de página e agrupados os controles de paginação para quebrar corretamente em 320 px.
- Corrigida a checagem da prévia de próximos atendimentos do dashboard para não contar linhas de outros painéis.
- Corrigidas cinco referências a SVGs inexistentes; o runner espera carregamento e valida dimensões naturais de todas as imagens.
- Ampliada a arte dos cabeçalhos ilustrados com ações no espaço disponível. A altura do conteúdo permanece estável e a regra responsiva restaura o tamanho relativo em tablet/mobile.
- Compactada a lista de próximos atendimentos; o rodapé do dashboard termina em Y=880,8 px no viewport 1768×890 e permanece dentro da captura.
- Removida uma regra de margem negativa sem componente correspondente.
- Corrigida a expectativa de título do runner geral: a tela de especialidades publica o heading acessível “Especialidades”. A captura local completa validou 93/93 telas/formatos em PostgreSQL descartável limpo.
- Alinhado o filtro do dashboard da Recepção com a referência: o seletor filtra situação, e a busca server-side cobre nome de paciente, profissional, telefone/CPF e horário local explícito `HH:MM`. Para evitar que um `on_change` atrasado restaure uma consulta antiga, o campo usa valor inicial do navegador e só submete seu valor nativo no Enter; limpar redefine o campo no cliente e o filtro no servidor. Um número de geração descarta respostas de recarga superadas. Testes unitários e Chromium cobrem o fluxo depois de paginação, busca por profissional e limpeza.
- Eliminada a URL duplicada nos dados da listagem de pacientes; cada link de ficha deriva do ID persistido da linha. O Chromium aguarda os resultados de busca e confirma que `href`, URL e nome da ficha pertencem ao mesmo paciente.
- Recomposta a área Financeira com métricas em uma linha, filtros de 36 px no desktop, respiro explícito em grids/flex, campos de 44 px em mobile, tabela semântica de seis colunas e vazio horizontal. O valor da cobrança e a evolução continuam ligados aos States existentes.
- Corrigidos os gaps numéricos inválidos das grades Reflex em telas de pacientes, calendário, agenda, especialidades, equipe, administração e Recepção; os espaços renderizam explicitamente em múltiplos de 4 px. A grade do cadastro do paciente mede 24 px entre formulário e orientações.
- Alinhadas as variantes de sidebar com as referências: recepção diária 48 px, agenda 64 px, pacientes/fila 80 px; a área desktop do cadastro começa em X=159 e mede 1.530 px.
- Corrigidos gaps Financeiros que eram descartados pelo browser como `normal`: os componentes Flex/Grid usam unidades CSS válidas. Em 1768×890, o conteúdo mede x=169/largura=1554 px; indicadores, filtros, emissão, cobranças e evolução iniciam em y=167,4/262,6/411/563/783 px.
- Encurtado o cabeçalho da tabela de cobranças para 33,5 px, ajustando a altura total da seção em conjunto com o espaço interno. A evolução termina dentro da primeira dobra conforme a referência.
- Refinados o padding e a altura dos estados vazios médicos e o ritmo da visão geral médica sem alterar as projeções clínicas autorizadas.
- Corrigida a captura de `/admin/funcionarios`: o teste de paginação rolava o conteúdo e cortava o título no PNG; o runner agora retorna ao topo e remove foco transitório antes de cada screenshot.

## Responsividade, acessibilidade e funcionamento

As seis larguras foram exercitadas em todas as rotas. As capturas finais confirmaram URL/título esperado, imagens carregadas e ausência de overflow horizontal. A execução de Chromium (`qa_browser/prescription_browser.py` e `qa_browser/admin_agenda_browser.py`) cobre foco, teclado e Escape em diálogos, ações de agenda, autorização, cadastro, busca, paginação, marcação e responsividade.

Permanecem os limites do estado funcional real documentados acima. A captura não altera dados clínicos para coincidir com os PNGs e o runner de rota não substitui os testes de autorização/fluxo.

## Testes e gates

| Verificação | Resultado final |
|---|---|
| `python -m pytest -q -rs` em PostgreSQL 16.16 de teste `vitta_one_test` | **572 passed, 3 skipped** em 40,30 s; 1 aviso `StarletteDeprecationWarning` do `httpx` no `TestClient`. Os skips são dois casos de concorrência/row-locking fora do ambiente CI próprio e um caso que recusa fixtures de concorrência fora de `vitta_one`. |
| `python -m pytest qa_browser/prescription_browser.py qa_browser/admin_agenda_browser.py -q` em PostgreSQL QA isolado `vitta_one_operational_ui_qa_14` | **42 passed** em 180,89 s; inclui autorização, fluxos clínicos/administrativos, foco, teclado, redução de movimento, responsividade e a regressão da busca vazia após buscar profissional |
| Regressão do link da ficha em Chromium | **5/5 repetições PASS** na primeira fixture; **1/1 PASS** na fixture limpa usada para a captura final; o teste confere ID esperado, URL e nome da ficha |
| `python -m qa_browser.capture_all_screens` em fixture sintética da rodada CI anterior | **93/93 PASS** no run CI histórico #342; este runner não foi repetido localmente após as últimas correções de Financeiro |
| `python -m qa_browser.capture_operational_reference_screens` com 16 referências locais em PostgreSQL QA recém-criado `vitta_one_operational_ui_qa_14` | **96/96 PASS**; 16 rotas em seis viewports, mais comparativos desktop lado a lado, overlays de 50%, diffs sem máscaras e quatro folhas gerados e inspecionados após reset de rolagem |
| Chromium CI #342 no commit `4523450` | **PASS**: 37 testes funcionais em 134,34 s, 5 testes de agenda em 14,86 s, 93/93 capturas gerais e 96/96 capturas operacionais |
| Auditoria final de viewport equivalente a zoom 200% | **16/16 PASS** em 884×445 na rodada final QA6; sem overflow global e sem imagens quebradas |
| `reflex compile --dry` com o ambiente PostgreSQL QA isolado | **PASS**, compilado em 6,164 s; persistem avisos existentes de depreciação Reflex e anotações de `on_submit` |
| `python -m compileall -q vitta_one qa_browser scripts tests` | **PASS** |
| OpenSpec strict | **34 passed, 0 failed**, 1 nota informativa sobre target spec arquivada de `patient-portal` |
| `git diff --check` | **PASS** |
| Migrations do banco descartável | `reflex db migrate` confirmou o schema da branch na base QA14; `alembic current --check-heads` confirmou `f031a5aa5002 (head)`; nenhuma migration nova nesta change |
| CI no SHA `2ee85798be7b5022f756e47438c1bb75303181c7` | **3/3 PASS**: OpenSpec/migrations/pytest/Reflex/smoke, Validate Vitta-One e QA Prescrições com Chromium; o Chromium completou 37 testes gerais, 5 de agenda, 93/93 capturas gerais e 96/96 capturas operacionais |

Depois do Chromium verde no commit de código `9c0bc1f`, o run de `b16c372` reproduziu falha na busca vazia da Recepção após paginação e busca por profissional. A separação tentativa entre rascunho e filtro ainda mantinha o campo controlado por evento Reflex; em execução longa o valor visual podia voltar ao termo anterior. A correção final retirou a atualização por caractere: o formulário lê o valor nativo submetido no Enter, inclusive vazio, enquanto a limpeza também redefine o campo no DOM. Um contador descarta reloads antigos. O teste unitário valida valores vazios/ausentes e submissão nova; o Chromium confirma campo vazio, oito linhas da página e total restaurado para 24. No código atual: Pytest 572 aprovados e 3 skips explicados; Chromium 42/42; captura limpa 96/96 em QA14. Nenhum banco/container preexistente ou de produção foi apagado; as bases QA11–QA14 foram criadas separadamente, migradas e semeadas somente com dados sintéticos.

## CI e revisão da PR

Na primeira tentativa Chromium do commit `a6583de`, um teste de 37 teve timeout na navegação para ficha do paciente. A repetição do job passou 37/37 testes funcionais, mas a captura geral encontrou uma expectativa antiga de título (“Todas as especialidades”) e validou 90/93; o runner foi corrigido em `a78b540`. No SHA `a78b5405309c565f689d830115dc78a96f6fab43`, os três workflows passaram (#537, #15 e #338) com 37 testes funcionais, 5 testes de agenda, 93/93 capturas gerais e 96/96 capturas operacionais.

Depois, os runs Chromium #339, #340 e #341 voltaram a falhar em `test_reception_global_patient_search_uses_identity_only`. A instrumentação do run #341 mostrou que a ação da linha “Paciente QA Operação 01” navegou para `/recepcao/pacientes/12` e carregou “Paciente QA Operação 11”. O commit `4523450` removeu a URL derivada duplicada do payload de listagem, constrói o link com o ID persistido da própria linha e fortalece o teste para aguardar os resultados, validar o ID/`href`/URL e confirmar o mesmo nome na ficha. O teste passou em cinco repetições locais e numa fixture recém-semeada; o Chromium CI #342 passou os 37 testes, os 5 testes de agenda e todas as capturas gerais e operacionais. `Validate Vitta-One` #541 e `Vitta One | CI Produção` #19 também passaram no commit `4523450`.

O artifact sintético do Chromium #342 está em [capturas e evidências do workflow](https://github.com/vitta-one/openspec/actions/runs/44801449817/artifacts/14660519772). Como os PNGs originais são mantidos fora do Git, a execução de CI valida somente as capturas; as comparações locais sem máscaras foram feitas com `VITTA_ONE_REFERENCE_DIR=qa-artifacts/reference`, geradas e inspecionadas em `qa-artifacts/operational-reference/`.

No SHA `9c0bc1f37feb6a27cd3fb272e5718bbea64425c0`, os três workflows pós-push passaram: Validate Vitta-One **#543**, Vitta One | CI Produção **#21** e QA Prescrições com Chromium **#344**. O Chromium validou 37 testes funcionais, 5 testes de agenda, 93/93 capturas gerais e 96/96 capturas operacionais; a etapa CI informa explicitamente que as referências originais não estavam no runner e que suas 96 capturas não representam comparação visual. O artifact [vitta-one-chromium-all-screens — run #344](https://github.com/vitta-one/openspec/actions/runs/44835423005/artifacts/14676784883) contém as capturas sintéticas e manifestos; comparativos com as referências permanecem no workspace local ignorado.

No SHA final de código `2ee85798be7b5022f756e47438c1bb75303181c7`, os três workflows também passaram: OpenSpec/migrations/pytest/Reflex/smoke [#44843172226](https://github.com/vitta-one/openspec/actions/runs/44843172226), Validate Vitta-One [#44843172261](https://github.com/vitta-one/openspec/actions/runs/44843172261) e QA Prescrições com Chromium [#44843172272](https://github.com/vitta-one/openspec/actions/runs/44843172272). A CI executou 37 testes funcionais, 5 de agenda, 93/93 capturas gerais e 96/96 capturas operacionais. O artifact [vitta-one-chromium-all-screens — run #44843172272](https://github.com/vitta-one/openspec/actions/runs/44843172272/artifacts/14682266453) contém capturas e manifestos sintéticos. Os logs registram que as referências PNG não estão disponíveis no runner; portanto, as capturas da CI não são comparação visual. As comparações reais sem máscaras foram geradas e inspecionadas localmente em `qa-artifacts/operational-reference/`.

A PR [#358](https://github.com/vitta-one/openspec/pull/358) aponta para `develop` e permanece aberta. Nenhum merge foi feito. Não houve migration de produção, deploy ou alteração de banco de produção.

## Validação final após correções — 21/11/2026

Esta rodada foi feita com código da branch de trabalho, Reflex em build local `--env prod` e PostgreSQL 16 descartável novo (`vitta_one_operational_ui_qa_20`), já migrado até `f031a5aa5002 (head)`. A referência original 01 foi alinhada proporcionalmente em um quadro 1768×890, sem deformação ou máscaras; as demais referências mantiveram 1768×890. As 96 capturas foram recriadas depois das alterações finais do CSS/serviço. Os quatro comparativos e overlays foram reabertos e inspecionados.

| Rota | Capturas | Diferença de pixels ≥ RGB L1 36 | MAE RGB/canal | Resultado visual |
|---|---:|---:|---:|---|
| 01 `/recepcao` | 6/6 | 16,07% | 13,49 | Revisada; conteúdo e indicadores sintéticos divergem |
| 02 `/recepcao/agenda` | 6/6 | 13,41% | 10,42 | Revisada; as 24 consultas sintéticas do dia concentram-se no sábado, enquanto a referência distribui eventos na semana |
| 03 `/recepcao/pacientes` | 6/6 | 10,17% | 12,06 | Revisada; lista e nomes sintéticos diferem |
| 04 `/recepcao/pacientes/novo` | 6/6 | 7,56% | 8,59 | Revisada; formulário inicia vazio; ilustração, ícones e landmarks refinados nesta iteração; continua sem aprovação pixel-idêntica |
| 05 `/recepcao/fila` | 6/6 | 10,73% | 11,19 | Revisada; há uma entrada de QA persistida, enquanto a referência mostra fila vazia |
| 06 `/admin` | 6/6 | 13,65% | 10,15 | Revisada; números/dados e 13 especialidades sintéticas diferem das 6 da referência |
| 07 `/admin/funcionarios` | 6/6 | 9,64% | 8,70 | Revisada; quantidade e dados de funcionários sintéticos diferem |
| 08 `/admin/funcionarios/novo` | 6/6 | 7,93% | 8,24 | Revisada; formulário vazio, banner reproduzido com o ativo correspondente |
| 09 `/admin/especialidades` | 6/6 | 11,34% | 11,06 | Revisada; há 13 especialidades sintéticas contra 6 na referência |
| 10 `/admin/horarios` | 6/6 | 7,15% | 6,67 | Revisada; nenhum profissional é pré-selecionado e nenhum horário é inventado |
| 11 `/admin/configuracoes` | 6/6 | 10,34% | 10,42 | Revisada; clínica de QA ainda sem configuração persistida; campos vazios |
| 12 `/financeiro` | 6/6 | 9,64% | 9,37 | Revisada; não há cobranças elegíveis na fixture, então totais/tabela ficam vazios/zero |
| 13 `/medico` | 6/6 | 8,07% | 8,04 | Revisada; a fila compartilhada tem uma entrada sintética e não há atendimento ativo deste médico |
| 14 `/medico/agenda` | 6/6 | 6,82% | 7,56 | Revisada; projeção autorizada deste médico não contém consultas; landmarks medidos no DOM |
| 15 `/medico/pacientes` | 6/6 | 4,14% | 5,53 | Revisada; não há pacientes vinculados a este médico na fixture; landmarks medidos no DOM |
| 16 `/medico/prontuarios` | 6/6 | 5,15% | 5,94 | Revisada; não existe prontuário/atendimento ativo para esta identidade; landmarks medidos no DOM |

Resultado da matriz: **96/96 PASS**, 0 falhas de captura e overflow global, 96 imagens carregadas. Comparações desktop: **16/16 geradas, 16/16 inspecionadas, 0/16 aprovadas como paridade visual integral**. A avaliação continua `REVIEW_REQUIRED`. A diferença RGB L1≥36 varia de **4,14% a 16,07%** (média **9,83%**); MAE médio por canal **9,51**. Essas métricas incluem dados, texto, estados, arte e rasterização, e não são uma nota automática de layout.

As ilustrações específicas das referências foram extraídas em recortes locais dedicados para banners e estados vazios das telas de Recepção, Administração, Financeiro e Médico; não são referências completas usadas como imagem de fundo. Os 15 ativos acrescentados são PNGs de componentes/arte e permanecem no Git. PNGs originais, capturas, comparativos, overlays e diffs permanecem ignorados pelo Git em `qa-artifacts/operational-reference/`. Folhas: `comparativo-01-04.png`, `comparativo-05-08.png`, `comparativo-09-12.png`, `comparativo-13-16.png`; cada rota tem também captura, `side-by-side.png`, `overlay-50.png` e `diff-amplified-3x.png`.

Diferenças de dados não foram convertidas em registros falsos para coincidir com os PNGs: não foram adicionadas cobranças, vínculos médicos, consultas ou registros clínicos para a comparação. Os resultados de cada fixture acima são distintos da avaliação de geometria. A versão 01 da fixture de agenda concentra 24 consultas no dia corrente para exercitar a tabela diária; isso explica a concentração no sábado em `/recepcao/agenda` e não é um ajuste de layout.

## Regressões funcionais encontradas e corrigidas nesta rodada

- Uma emissão financeira concorrente podia passar pela validação inicial, resolver o cliente externo com commits intermediários e tentar inserir a cobrança sem consultar novamente a consulta bloqueada. O serviço agora revalida a existência de cobrança ativa depois de readquirir o lock da consulta, preservando o índice único como última proteção. Um teste determinístico reproduziu a tentativa dupla no SQLite e PostgreSQL antes da correção e confirmou que apenas a cobrança concorrente permanece, sem chamada externa de pagamento, depois dela.
- O browser QA de agendamento agora abre a semana que contém o horário escolhido. Isso cobre a borda de semana: em 21/11/2026, a fixture de agendamento inicia dois dias depois e cai na semana seguinte. A verificação não depende de a data corrente ser segunda-feira.
- Auditoria do CSS removeu uma regra responsiva médica duplicada e uma redefinição redundante do ícone de estado vazio. Os valores computados permanecem os da regra efetiva já comparada.

## Validação técnica final desta rodada

| Validação | Resultado |
|---|---|
| Pytest completo em `vitta_one_test` PostgreSQL descartável | **574 passed, 3 skipped**, 1 `StarletteDeprecationWarning` legado |
| Chromium funcional, autorização, acessibilidade de teclado/foco e responsividade | **42 passed** em 172,96 s; inclui o fluxo de agendamento após correção de semana |
| OpenSpec strict | **34 passed, 0 failed**, com nota informativa preexistente sobre target spec arquivada de `patient-portal` |
| `python -m compileall -q vitta_one qa_browser scripts tests` | **PASS** |
| `reflex compile --dry` | **PASS** em 7,330 s; continuam avisos de APIs/assinaturas Reflex depreciadas |
| `git diff --check` | **PASS** após a atualização do relatório e OpenSpec |
| Migrações no banco QA20 | `reflex db migrate` concluído; `alembic current --check-heads` em `f031a5aa5002 (head)` |
| Build de produção local e smoke HTTP | **PASS**, `/login` respondeu HTTP 200 após seguir o redirecionamento canônico |

Os três skips e o aviso HTTP continuam explicados na rodada anterior. `alembic check` segue sem poder comparar metadata neste repositório porque `alembic/env.py` não fornece `target_metadata`; não foi criada migration nem alterado schema de produção. O build local avisou que Reflex detecta diferenças de schema que pediriam `reflex db makemigrations`, mas o estado migrado confirmado continua no head Alembic e nenhuma migration nova foi necessária para esta correção.

A fidelidade visual integral permanece **não aprovada (0/16)**. A próxima aprovação depende de avaliar e resolver diferenças reais restantes com os contratos de domínio intactos; em especial, os estados/dados de referência divergem das projeções autorizadas e sintéticas e não foram imitados com dados falsos.

## Isolamento da captura Chromium — 21/11/2026

O CI Chromium #44866103623 chegou a **95/96 capturas**. A falha foi `/medico/pacientes` em 1768×890: o landmark do estado vazio estava ausente porque `test_patient_books_own_appointment_and_both_staff_agendas_update` tinha agendado uma consulta sintética para o Médico B antes da matriz. O seed inicial preserva intencionalmente esse médico sem pacientes vinculados para validar o estado vazio; a captura executada depois dos testes funcionais herdava a mutação.

O workflow agora roda e exige a matriz de 16 telas imediatamente após subir o servidor, antes dos testes interativos que alteram a fixture. A captura continua sendo gerada pelo build corrente, sem relaxar landmarks ou criar dados artificiais para a tela; os demais testes continuam executando mesmo se a etapa de captura falhar, e a falha é verificada ao fim do job. No SHA `149f25cf8f4f2d0c4a52d1e475107301baccc372`, o CI Chromium #44867148239 confirmou a correção: **96/96** capturas operacionais, **37** testes de navegador, **5** testes de agenda e **93/93** capturas gerais passaram. O artifact [vitta-one-chromium-all-screens — run #44867148239](https://github.com/vitta-one/openspec/actions/runs/44867148239/artifacts/14692179081) contém somente as capturas sintéticas e manifestos; referências originais não estão disponíveis no runner, então isso não representa comparação visual. A avaliação local continua em **0/16 telas aprovadas**.

## Refinamento adicional da tela Novo paciente — 21/11/2026

A revisão rejeitou a tela 04. A comparação sem máscaras mostrou defeitos geométricos ainda corrigíveis, então a tela foi medida novamente, alterada e recapturada com Chromium do bundle atual.

| Marco em 1768×890 | Medida atual | Evidência/ajuste |
|---|---:|---|
| Área de conteúdo | x=159, largura=1530 px | Mesmo eixo e limite horizontal da referência |
| Cartão do formulário | x=159, y=267 px, largura=905 px | Conteúdo interno começa em x=186 e mede 851 px |
| Painel de orientação | x=1088, y=267 px, largura≈601 px | Recorte da ilustração ocupa 599×249 px sem distorção |
| Campos | nome y=421, CPF y=534, telefone y=673 px | Cada controle mede 851×50 px |
| Ícones dos campos | x=210 px (caixa SVG) | A regra final anterior deixava os glifos aproximadamente 10 px à esquerda |
| Divisória e ações | divisória y=752 px; ações y=777 px | Cancelar 130×48 px e cadastrar 250×48 px; antes estavam 3 px abaixo |
| Placeholder a 320 px | texto medido 173,0 px; área disponível 175,2 px | O texto completo cabe; o runner falha se o placeholder ultrapassar o campo |

O ícone de orientação deixou de receber um círculo CSS redundante ao redor do próprio símbolo circular; as dicas usam um check simples, o ícone de dados pessoais foi ampliado e a ação principal recebeu o peso tipográfico da referência. A comparação ampliada confirmou que as três quebras do texto orientativo, a divisória e o eixo das dicas permanecem alinhados.

A matriz atual, executada após essas alterações, concluiu **96/96 capturas PASS** nos seis tamanhos, sem imagens quebradas, falhas de rota ou overflow horizontal global. Foram gerados e inspecionados os 16 comparativos desktop, overlays e diffs sem máscaras. Na tela 04, o diff RGB L1≥36 caiu de **13,09% (MAE/canal 13,32)** na rodada anterior para **7,56% (MAE/canal 8,59)**. Isso comprova melhoria, não igualdade: a tela permanece `REVIEW_REQUIRED` e a avaliação geral segue **0/16 aprovada integralmente**.

O overlay atual em `qa-artifacts/operational-reference/comparisons/04-novo-paciente/` ainda mostra diferenças de rasterização, formas dos ícones/navegação, superfícies e texto. As outras 15 comparações foram reabertas; permanecem os desvios de conteúdo e estado por rota descritos nas tabelas. Nenhum registro de paciente, consulta, fila, prontuário, exame ou cobrança foi adicionado, removido ou alterado para reduzir o diff.

## Recaptura e inspeção corrente — 21/11/2026, QA22

Depois do endurecimento do guard de banco, o bundle da branch foi iniciado novamente em build `--env prod`, agora contra o PostgreSQL 16 descartável `vitta_one_operational_ui_qa_22`, migrado até `f031a5aa5002 (head)` e semeado com fixtures QA sintéticas. O capturador confirmou o build local servido em `127.0.0.1:3000` e concluiu **96/96** capturas, sem falha de navegação, imagem quebrada ou overflow horizontal. Os 16 overlays de 50%, diffs sem máscara e comparativos lado a lado foram regenerados; as quatro folhas agregadas foram reabertas para inspeção.

| Tela | Pixels com RGB L1 ≥ 36 | MAE RGB/canal | Inspeção |
|---|---:|---:|---|
| 01 `/recepcao` | 16,06% | 13,49 | Revisada; dados/estados sintéticos divergem |
| 02 `/recepcao/agenda` | 13,41% | 10,42 | Revisada; datas e distribuição de consultas diferem |
| 03 `/recepcao/pacientes` | 10,17% | 12,06 | Revisada; nomes e quantidade de pacientes diferem |
| 04 `/recepcao/pacientes/novo` | 7,56% | 8,59 | Revisada após refinamento; persistem diferenças visuais e de rasterização |
| 05 `/recepcao/fila` | 10,73% | 11,19 | Revisada; fixture tem uma entrada e a referência está vazia |
| 06 `/admin` | 13,65% | 10,15 | Revisada; métricas e especialidades diferem |
| 07 `/admin/funcionarios` | 9,64% | 8,70 | Revisada; dados e quantidade de funcionários diferem |
| 08 `/admin/funcionarios/novo` | 7,93% | 8,24 | Revisada; formulário vazio e diferenças residuais de arte/texto |
| 09 `/admin/especialidades` | 11,34% | 11,06 | Revisada; fixture tem 13 especialidades, a referência mostra 6 |
| 10 `/admin/horarios` | 7,15% | 6,67 | Revisada; sem profissional selecionado, sem horários inventados |
| 11 `/admin/configuracoes` | 10,34% | 10,42 | Revisada; configuração clínica de QA vazia |
| 12 `/financeiro` | 9,64% | 9,37 | Revisada; não há cobranças elegíveis na fixture |
| 13 `/medico` | 8,07% | 8,04 | Revisada; fila compartilhada sintética contém uma entrada |
| 14 `/medico/agenda` | 6,82% | 7,56 | Revisada; médico QA não tem consultas vinculadas |
| 15 `/medico/pacientes` | 4,14% | 5,53 | Revisada; médico QA não tem pacientes vinculados |
| 16 `/medico/prontuarios` | 5,15% | 5,94 | Revisada; médico QA não tem prontuário ativo |

Na matriz corrente, pixels alterados acima do limiar variam de **4,14% a 16,06%** (média **9,49%**); MAE médio por canal: **9,21**. Esses valores incluem texto, conteúdo, estados, ícones e rasterização. `fidelity-assessment.json` continua `REVIEW_REQUIRED`: **0/16 telas aprovadas**. Não declaro identidade pixel a pixel.

Uma comparação técnica temporária de fonte, só na tela 04, sem mudança de produto, mostrou que Inter reduz o MAE total de 8,59 para 8,44, mas aumenta pixels alterados e piora a região textual do painel orientativo. A pilha tipográfica do produto foi mantida porque a alteração global não demonstrou ganho consistente.

O guard de captura permite o banco dedicado `vitta_one_operational_ui_qa_22` na porta local reservada e recusa o nome genérico `vitta_one` nessa porta. O teste direcionado do guard passou **3/3**. Banco, capturas e comparativos permanecem em QA local ignorado pelo Git; nenhum registro clínico ou financeiro foi manipulado para coincidir com a referência.

### Regressão funcional repetida após a recaptura

- Pytest completo em PostgreSQL 16 descartável novo `vitta_one_test_22`, migrado a `f031a5aa5002 (head)`: **574 passed, 3 skipped** em 35,07 s. Os skips são os cenários de concorrência/row-locking não habilitados por este banco fora do nome `vitta_one`; um aviso `StarletteDeprecationWarning` legado permanece.
- Chromium de autorização, formulários, agenda, foco/teclado e responsividade no servidor recém-compilado contra QA22: **42 passed** em 173,81 s.
- Depois dessas execuções, permanecem válidos os gates repetidos: guard QA **3/3**, OpenSpec strict **34 passed, 0 failed**, `compileall`, `reflex compile --dry` e `git diff --check` aprovados. O servidor de comparação usa somente QA22 local; nenhuma conexão de produção foi configurada.
