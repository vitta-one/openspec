# Relatório final de paridade visual das telas operacionais — 20/11/2026

## Escopo e método

Continuação do checkpoint `bfe77d9001a875574f39b8aafb89859d4ad5beff` na branch `fix/visual-parity-16-screens-20261117`. A implementação permaneceu em Reflex, preservando States, handlers server-side, modelos, serviços e autorização existente.

As 16 referências PNG anexadas foram copiadas para `qa-artifacts/reference/`, ignorado pelo Git. Cada arquivo foi conferido por SHA-256 contra o anexo com o mesmo número/nome. A referência 01 mede 1774×887; ela foi ajustada proporcionalmente com `contain` ao quadro 1768×890, com faixa de 3 px no eixo Y. As outras 15 já medem 1768×890. Não foram aplicadas máscaras. As capturas finais são do Chromium usando o código final desta branch.

O runner `qa_browser.capture_operational_reference_screens` registrou dimensões e caixas via `getBoundingClientRect()`, estilos computados, imagens carregadas, URL, títulos e overflow. Foram gerados PNGs, lado a lado, overlays a 50%, diffs amplificados e quatro folhas de comparação em `qa-artifacts/operational-reference/` (ignorado pelo Git). As quatro folhas com as 16 telas foram inspecionadas visualmente após a captura final. Métricas de pixels são diagnósticas e contam também conteúdo, texto, dados e variações de rasterização; não representam uma nota de fidelidade.

## Status de evidência

| Evidência | Resultado |
|---|---|
| Capturas concluídas | **96/96 PASS**, 16 rotas × seis viewports; sem falhas de navegação ou overflow horizontal global |
| Carregamento das imagens | **96/96** capturas sem imagens quebradas; todas completas e com `naturalWidth > 0` |
| Smoke de rota e controles | **16/16 PASS** no navegador, com agenda, paginação de recepção e filtros de especialidades incluídos |
| Comparações geradas | **16/16** com referência alinhada, lado a lado, overlay e diff; sem máscaras |
| Comparações inspecionadas | **16/16**, após a última alteração de escala da arte |
| Aprovação visual integral | **0/16**; todas as 16 foram inspecionadas, mas ainda têm diferenças residuais de conteúdo, arte ou composição descritas abaixo |
| Aprovação como pixel-idêntica | **0/16**; não se declara identidade visual sem comprovação |
| Reflow equivalente a 200% | **16/16 PASS** em viewport CSS 884×445, sem overflow ou imagens quebradas |

Os comparativos individuais e manifestos detalhados permanecem em `qa-artifacts/operational-reference/`. A escala de 200% foi verificada como viewport CSS reduzido à metade, não por alteração do zoom do sistema operacional.

## Avaliação por tela

| # / rota | Captura e navegação | Inspeção visual e diferenças residuais |
|---|---|---|
| 01 `/recepcao` | 6/6; rota PASS | Grade, KPIs, consultas e painéis mantêm a hierarquia da referência. O painel de próximos atendimentos foi compactado para que o rodapé completo caiba no quadro de 890 px. Contagens e quantidade de consultas vêm da fixture sintética e divergem; layout não é pixel-idêntico. Pixels alterados: 15,77%; MAE RGB: 12,73. |
| 02 `/recepcao/agenda` | 6/6; rota PASS | Calendário semanal e navegação estão funcionais. Distribuição dos horários difere porque as consultas sintéticas se concentram em dias distintos da imagem. Pixels alterados: 13,22%; MAE: 10,32. |
| 03 `/recepcao/pacientes` | 6/6; rota PASS | Busca, tabela e paginação renderizam. A fixture contém mais pacientes que a referência, alongando a tabela. A arte SVG disponível não reproduz exatamente a ilustração original; a arte no cabeçalho foi ampliada no espaço livre sem mover o painel. Pixels alterados: 11,12%; MAE: 12,51. |
| 04 `/recepcao/pacientes/novo` | 6/6; rota PASS | Formulário em duas colunas, campos e dicas seguem a composição; texto auxiliar e arte são próprios da aplicação e não são idênticos aos PNGs. Pixels alterados: 12,82%; MAE: 13,31. |
| 05 `/recepcao/fila` | 6/6; rota PASS | A referência mostra fila vazia; a fixture contém um atendimento sintético aguardando e, portanto, mostra linha e ações. A composição da fila, filtros e métricas continua utilizável; cabeçalho ilustrado ampliado sem deslocar o painel. Pixels alterados: 12,18%; MAE: 12,03. |
| 06 `/admin` | 6/6; rota PASS | Grupos, cartões e atalhos seguem a estrutura da referência. Contagens sintéticas diferem (incluindo 13 especialidades versus 6) e a arte SVG é uma recriação própria. Pixels alterados: 13,79%; MAE: 10,33. |
| 07 `/admin/funcionarios` | 6/6; rota PASS | Busca, tabela e paginação funcionam. Quantidade e valores de funcionários divergem da imagem. Corrigido o valor inicial do seletor Radix para tamanho de página e o rodapé agora quebra em telas de 320 px sem overflow. Pixels alterados: 9,70%; MAE: 8,71. |
| 08 `/admin/funcionarios/novo` | 6/6; rota PASS | Hierarquia e formulário preservados. Banner usa a arte vetorial disponível, que difere da original. Pixels alterados: 8,66%; MAE: 8,66. |
| 09 `/admin/especialidades` | 6/6; rota PASS | Pesquisa e filtro estão alinhados: ambos em Y=369,75 px, altura computada de 40 px, diferença vertical de **0 px**. A fixture tem 13 especialidades, contra 6 na referência; a quantidade de registros e linhas difere. Pixels alterados: 11,39%; MAE: 11,07. |
| 10 `/admin/horarios` | 6/6; rota PASS | Estado sem profissional selecionado corresponde à composição vazia da referência. Arte decorativa é uma recriação SVG. Pixels alterados: 7,84%; MAE: 7,37. |
| 11 `/admin/configuracoes` | 6/6; rota PASS | Layout de formulário e painel de orientação renderizado. A fixture está sem dados da clínica, então os campos aparecem vazios em vez de preenchidos como na referência; não foram inventados dados de clínica. Pixels alterados: 10,79%; MAE: 11,01. |
| 12 `/financeiro` | 6/6; rota PASS | Filtros, emissão e recebimentos renderizam. A fixture não tem cobranças elegíveis; valores, datas e linhas são diferentes da referência. Não foram criadas cobranças para simular a imagem. Banner corrigido para o SVG existente. Pixels alterados: 12,08%; MAE: 11,94. |
| 13 `/medico` | 6/6; rota PASS | Painel médico, atalhos e estado de atendimento funcionam. A fila sintética compartilhada exibe 1 paciente, enquanto a referência mostra fila vazia; não há atendimento ativo para esta identidade de QA. Arte não é o ativo original. Pixels alterados: 16,03%; MAE: 13,62. |
| 14 `/medico/agenda` | 6/6; rota PASS | Calendário semanal e mensal renderizam. A identidade de QA escolhida não tem consultas agendadas, ao contrário das consultas exibidas na referência; não foram criadas consultas só para a captura. Pixels alterados: 12,85%; MAE: 11,57. |
| 15 `/medico/pacientes` | 6/6; rota PASS | Lista e estado vazio estão funcionais. O médico de QA não tem pacientes vinculados; a referência contém registros. Não foram inventados vínculos clínicos. Pixels alterados: 14,60%; MAE: 11,84. |
| 16 `/medico/prontuarios` | 6/6; rota PASS | Estado sem prontuário ativo renderiza sem erros. A arte e a geometria do painel têm diferenças visíveis em relação à referência. Não foram criados prontuários/diagnósticos fictícios. Pixels alterados: 14,14%; MAE: 11,21. |

### Diferenças que permanecem

- As imagens ilustrativas são SVGs próprios existentes no projeto, não os ativos originais. Cinco referências quebradas para `/clinic-building-hero.svg` e `/clinic-building-guide.svg` foram corrigidas para o SVG existente `/clinic-operational-hero.svg`; a checagem de carregamento agora torna esse tipo de regressão explícito.
- Os dados de QA não são cópias dos valores dos PNGs. As diferenças de contagem, datas, registros, estado vazio e conteúdo estão discriminadas por rota acima e não foram ocultadas com máscaras.
- Os estados de cobrança real, envio Resend e webhook público não foram homologados: não há credenciais sandbox/providers nem endpoint HTTPS público neste ambiente. Os testes correspondentes usam os mocks existentes.
- As comparações finais registram diferenças de pixels entre 7,84% e 16,03% no limiar RGB L1=36. Isso inclui conteúdo/data, texto, arte e renderização, não isola apenas geometria. Todas as 16 comparações foram inspecionadas; nenhuma recebeu aprovação visual integral ou identidade pixel a pixel, e as diferenças estruturais ainda visíveis estão discriminadas por rota.

## Correções aplicadas nesta continuação

- Corrigida a especificidade do seletor de pesquisa de especialidades; DOM final mede 40 px em ambos os campos e 0 px de desalinhamento vertical.
- Corrigido o valor do `Select` de tamanho de página e agrupados os controles de paginação para quebrar corretamente em 320 px.
- Corrigida a checagem da prévia de próximos atendimentos do dashboard para não contar linhas de outros painéis.
- Corrigidas cinco referências a SVGs inexistentes; o runner espera carregamento e valida dimensões naturais de todas as imagens.
- Ampliada a arte dos cabeçalhos ilustrados com ações no espaço disponível. A altura do conteúdo permanece estável e a regra responsiva restaura o tamanho relativo em tablet/mobile.
- Compactada a lista de próximos atendimentos; o rodapé do dashboard termina em Y=880,8 px no viewport 1768×890 e permanece dentro da captura.
- Removida uma regra de margem negativa sem componente correspondente.
- Corrigida a expectativa de título do runner geral: a tela de especialidades publica o heading acessível “Especialidades”. A captura local completa validou 93/93 telas/formatos em PostgreSQL descartável limpo.
- Eliminada a URL duplicada nos dados da listagem de pacientes; cada link de ficha deriva do ID persistido da linha. O Chromium aguarda os resultados de busca e confirma que `href`, URL e nome da ficha pertencem ao mesmo paciente.

## Responsividade, acessibilidade e funcionamento

As seis larguras foram exercitadas em todas as rotas. As capturas finais confirmaram URL/título esperado, imagens carregadas e ausência de overflow horizontal. A execução de Chromium (`qa_browser/prescription_browser.py` e `qa_browser/admin_agenda_browser.py`) cobre foco, teclado e Escape em diálogos, ações de agenda, autorização, cadastro, busca, paginação, marcação e responsividade.

Permanecem os limites do estado funcional real documentados acima. A captura não altera dados clínicos para coincidir com os PNGs e o runner de rota não substitui os testes de autorização/fluxo.

## Testes e gates

| Verificação | Resultado final |
|---|---|
| `pytest -q` em PostgreSQL 16 descartável limpo `vitta_one_test` | **569 passed, 3 skipped**, 1 aviso de depreciação `StarletteDeprecationWarning` relacionado a `httpx` no `TestClient` |
| `pytest qa_browser/prescription_browser.py qa_browser/admin_agenda_browser.py -q` em `vitta_one_operational_ui_qa_20261120` | **42 passed** em 180,28 s; inclui fluxo clínico/administrativo, autorização, foco e teclado |
| Regressão do link da ficha em Chromium | **5/5 repetições PASS** na primeira fixture; **1/1 PASS** na fixture limpa usada para a captura final; o teste confere ID esperado, URL e nome da ficha |
| `python -m qa_browser.capture_all_screens` em `vitta_one_operational_ui_qa_2` recém-semeado | **93/93 PASS**; todas as rotas, perfis e viewports do runner geral |
| `python -m qa_browser.capture_operational_reference_screens` com `VITTA_ONE_REFERENCE_DIR=qa-artifacts/reference` em `vitta_one_operational_ui_qa_2` | **96/96 PASS**, sem falhas; 16 comparações desktop geradas e inspecionadas sobre dados sintéticos recém-semeados |
| Chromium CI #342 no commit `4523450` | **PASS**: 37 testes funcionais em 134,34 s, 5 testes de agenda em 14,86 s, 93/93 capturas gerais e 96/96 capturas operacionais |
| Auditoria de viewport equivalente a zoom 200% | **16/16 PASS** em 884×445 |
| `reflex compile --dry` com o ambiente PostgreSQL QA isolado | **PASS**, compilado em 6,328 s; há avisos preexistentes de depreciação Reflex e assinaturas de `on_submit` |
| `python -m compileall -q vitta_one qa_browser scripts tests` | **PASS** |
| OpenSpec strict | **34 passed, 0 failed**, 1 nota informativa sobre target spec arquivada de `patient-portal` |
| `git diff --check` | **PASS** |
| Migrations do banco descartável | `alembic upgrade head` passou até `f031a5aa5002`; nenhuma migration nova nesta change |

Uma primeira execução de Pytest foi feita acidentalmente contra o banco descartável já preenchido pelas fixtures de navegador e encontrou duas colisões: CPFs fixos dos testes de concorrência e um prontuário inexistente nesse estado. A suíte foi repetida em `vitta_one_test`, recém-criado e sem dados, e passou integralmente. A suíte Chromium completa rodou em outro banco descartável; a matriz final foi então gerada numa terceira base recém-migrada/semeada (`vitta_one_operational_ui_qa_2`), sem reutilizar os dados mutados pelos fluxos de navegador. Nenhum banco/container preexistente ou de produção foi alterado; as bases e contas QA são descartáveis/sintéticas.

## CI e revisão da PR

Na primeira tentativa Chromium do commit `a6583de`, um teste de 37 teve timeout na navegação para ficha do paciente. A repetição do job passou 37/37 testes funcionais, mas a captura geral encontrou uma expectativa antiga de título (“Todas as especialidades”) e validou 90/93; o runner foi corrigido em `a78b540`. No SHA `a78b5405309c565f689d830115dc78a96f6fab43`, os três workflows passaram (#537, #15 e #338) com 37 testes funcionais, 5 testes de agenda, 93/93 capturas gerais e 96/96 capturas operacionais.

Depois, os runs Chromium #339, #340 e #341 voltaram a falhar em `test_reception_global_patient_search_uses_identity_only`. A instrumentação do run #341 mostrou que a ação da linha “Paciente QA Operação 01” navegou para `/recepcao/pacientes/12` e carregou “Paciente QA Operação 11”. O commit `4523450` removeu a URL derivada duplicada do payload de listagem, constrói o link com o ID persistido da própria linha e fortalece o teste para aguardar os resultados, validar o ID/`href`/URL e confirmar o mesmo nome na ficha. O teste passou em cinco repetições locais e numa fixture recém-semeada; o Chromium CI #342 passou os 37 testes, os 5 testes de agenda e todas as capturas gerais e operacionais. `Validate Vitta-One` #541 e `Vitta One | CI Produção` #19 também passaram no commit `4523450`.

O artifact sintético do Chromium #342 está em [capturas e evidências do workflow](https://github.com/vitta-one/openspec/actions/runs/44801449817/artifacts/14660519772). Como os PNGs originais são mantidos fora do Git, a execução de CI valida somente as capturas; as comparações locais sem máscaras foram feitas com `VITTA_ONE_REFERENCE_DIR=qa-artifacts/reference`, geradas e inspecionadas em `qa-artifacts/operational-reference/`.

A PR #358 aponta para `develop`, permanece aberta e não foi mergeada. Não houve migration de produção, deploy ou alteração de banco de produção.
