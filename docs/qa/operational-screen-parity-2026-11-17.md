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

Depois do Chromium verde no commit de código `9c0bc1f`, o run de `b16c372` reproduziu falha na busca vazia da Recepção após paginação e busca por profissional. A separação tentativa entre rascunho e filtro ainda mantinha o campo controlado por evento Reflex; em execução longa o valor visual podia voltar ao termo anterior. A correção final retirou a atualização por caractere: o formulário lê o valor nativo submetido no Enter, inclusive vazio, enquanto a limpeza também redefine o campo no DOM. Um contador descarta reloads antigos. O teste unitário valida valores vazios/ausentes e submissão nova; o Chromium confirma campo vazio, oito linhas da página e total restaurado para 24. No código atual: Pytest 572 aprovados e 3 skips explicados; Chromium 42/42; captura limpa 96/96 em QA14. Nenhum banco/container preexistente ou de produção foi apagado; as bases QA11–QA14 foram criadas separadamente, migradas e semeadas somente com dados sintéticos.

## CI e revisão da PR

Na primeira tentativa Chromium do commit `a6583de`, um teste de 37 teve timeout na navegação para ficha do paciente. A repetição do job passou 37/37 testes funcionais, mas a captura geral encontrou uma expectativa antiga de título (“Todas as especialidades”) e validou 90/93; o runner foi corrigido em `a78b540`. No SHA `a78b5405309c565f689d830115dc78a96f6fab43`, os três workflows passaram (#537, #15 e #338) com 37 testes funcionais, 5 testes de agenda, 93/93 capturas gerais e 96/96 capturas operacionais.

Depois, os runs Chromium #339, #340 e #341 voltaram a falhar em `test_reception_global_patient_search_uses_identity_only`. A instrumentação do run #341 mostrou que a ação da linha “Paciente QA Operação 01” navegou para `/recepcao/pacientes/12` e carregou “Paciente QA Operação 11”. O commit `4523450` removeu a URL derivada duplicada do payload de listagem, constrói o link com o ID persistido da própria linha e fortalece o teste para aguardar os resultados, validar o ID/`href`/URL e confirmar o mesmo nome na ficha. O teste passou em cinco repetições locais e numa fixture recém-semeada; o Chromium CI #342 passou os 37 testes, os 5 testes de agenda e todas as capturas gerais e operacionais. `Validate Vitta-One` #541 e `Vitta One | CI Produção` #19 também passaram no commit `4523450`.

O artifact sintético do Chromium #342 está em [capturas e evidências do workflow](https://github.com/vitta-one/openspec/actions/runs/44801449817/artifacts/14660519772). Como os PNGs originais são mantidos fora do Git, a execução de CI valida somente as capturas; as comparações locais sem máscaras foram feitas com `VITTA_ONE_REFERENCE_DIR=qa-artifacts/reference`, geradas e inspecionadas em `qa-artifacts/operational-reference/`.

No SHA `9c0bc1f37feb6a27cd3fb272e5718bbea64425c0`, os três workflows pós-push passaram: Validate Vitta-One **#543**, Vitta One | CI Produção **#21** e QA Prescrições com Chromium **#344**. O Chromium validou 37 testes funcionais, 5 testes de agenda, 93/93 capturas gerais e 96/96 capturas operacionais; a etapa CI informa explicitamente que as referências originais não estavam no runner e que suas 96 capturas não representam comparação visual. O artifact [vitta-one-chromium-all-screens — run #344](https://github.com/vitta-one/openspec/actions/runs/44835423005/artifacts/14676784883) contém as capturas sintéticas e manifestos; comparativos com as referências permanecem no workspace local ignorado.

A PR [#358](https://github.com/vitta-one/openspec/pull/358) aponta para `develop` e permanece aberta. Nenhum merge foi feito. Não houve migration de produção, deploy ou alteração de banco de produção.
