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
| Aprovação como pixel-idêntica | **0/16**; diferenças residuais de conteúdo, arte e densidade são visíveis e documentadas abaixo |
| Reflow equivalente a 200% | **16/16 PASS** em viewport CSS 884×445, sem overflow ou imagens quebradas |

Os comparativos individuais e manifestos detalhados permanecem em `qa-artifacts/operational-reference/`. A escala de 200% foi verificada como viewport CSS reduzido à metade, não por alteração do zoom do sistema operacional.

## Avaliação por tela

| # / rota | Captura e navegação | Inspeção visual e diferenças residuais |
|---|---|---|
| 01 `/recepcao` | 6/6; rota PASS | Grade, KPIs, consultas e painéis mantêm a hierarquia da referência. O painel de próximos atendimentos foi compactado para que o rodapé completo caiba no quadro de 890 px. Contagens e quantidade de consultas vêm da fixture sintética e divergem; layout não é pixel-idêntico. Pixels alterados: 15,87%; MAE RGB: 12,77. |
| 02 `/recepcao/agenda` | 6/6; rota PASS | Calendário semanal e navegação estão funcionais. Distribuição dos horários difere porque as consultas sintéticas se concentram em dias distintos da imagem. Pixels alterados: 13,35%; MAE: 10,48. |
| 03 `/recepcao/pacientes` | 6/6; rota PASS | Busca, tabela e paginação renderizam. A fixture contém mais pacientes que a referência, alongando a tabela. A arte SVG disponível não reproduz exatamente a ilustração original; a arte no cabeçalho foi ampliada no espaço livre sem mover o painel. Pixels alterados: 11,14%; MAE: 12,52. |
| 04 `/recepcao/pacientes/novo` | 6/6; rota PASS | Formulário em duas colunas, campos e dicas seguem a composição; texto auxiliar e arte são próprios da aplicação e não são idênticos aos PNGs. Pixels alterados: 12,82%; MAE: 13,31. |
| 05 `/recepcao/fila` | 6/6; rota PASS | A referência mostra fila vazia; a fixture contém um atendimento sintético aguardando e, portanto, mostra linha e ações. A composição da fila, filtros e métricas continua utilizável; cabeçalho ilustrado ampliado sem deslocar o painel. Pixels alterados: 12,73%; MAE: 12,46. |
| 06 `/admin` | 6/6; rota PASS | Grupos, cartões e atalhos seguem a estrutura da referência. Contagens sintéticas diferem (incluindo 22 especialidades versus 6) e a arte SVG é uma recriação própria. Pixels alterados: 13,79%; MAE: 10,35. |
| 07 `/admin/funcionarios` | 6/6; rota PASS | Busca, tabela e paginação funcionam. Quantidade e valores de funcionários divergem da imagem. Corrigido o valor inicial do seletor Radix para tamanho de página e o rodapé agora quebra em telas de 320 px sem overflow. Pixels alterados: 10,97%; MAE: 10,06. |
| 08 `/admin/funcionarios/novo` | 6/6; rota PASS | Hierarquia e formulário preservados. Banner usa a arte vetorial disponível, que difere da original. Pixels alterados: 8,66%; MAE: 8,66. |
| 09 `/admin/especialidades` | 6/6; rota PASS | Pesquisa e filtro estão alinhados: ambos em Y=369,75 px, altura computada de 40 px, diferença vertical de **0 px**. A fixture tem 22 especialidades, contra 6 na referência, para exercitar paginação; os registros e a quantidade de linhas diferem. Pixels alterados: 11,34%; MAE: 10,99. |
| 10 `/admin/horarios` | 6/6; rota PASS | Estado sem profissional selecionado corresponde à composição vazia da referência. Arte decorativa é uma recriação SVG. Pixels alterados: 7,84%; MAE: 7,37. |
| 11 `/admin/configuracoes` | 6/6; rota PASS | Layout de formulário e painel de orientação renderizado. A fixture está sem dados da clínica, então os campos aparecem vazios em vez de preenchidos como na referência; não foram inventados dados de clínica. Pixels alterados: 10,79%; MAE: 11,01. |
| 12 `/financeiro` | 6/6; rota PASS | Filtros, emissão e recebimentos renderizam. A fixture não tem cobranças elegíveis; valores, datas e linhas são diferentes da referência. Não foram criadas cobranças para simular a imagem. Banner corrigido para o SVG existente. Pixels alterados: 12,57%; MAE: 12,56. |
| 13 `/medico` | 6/6; rota PASS | Painel médico, atalhos e estado de atendimento funcionam. A fila sintética compartilhada exibe 1 paciente, enquanto a referência mostra fila vazia; não há atendimento ativo para esta identidade de QA. Arte não é o ativo original. Pixels alterados: 16,04%; MAE: 13,63. |
| 14 `/medico/agenda` | 6/6; rota PASS | Calendário semanal e mensal renderizam. A identidade de QA escolhida não tem consultas agendadas, ao contrário das consultas exibidas na referência; não foram criadas consultas só para a captura. Pixels alterados: 12,86%; MAE: 11,61. |
| 15 `/medico/pacientes` | 6/6; rota PASS | Lista e estado vazio estão funcionais. O médico de QA não tem pacientes vinculados; a referência contém registros. Não foram inventados vínculos clínicos. Pixels alterados: 13,27%; MAE: 12,25. |
| 16 `/medico/prontuarios` | 6/6; rota PASS | Estado sem prontuário ativo renderiza sem erros. A arte e a geometria do painel têm diferenças visíveis em relação à referência. Não foram criados prontuários/diagnósticos fictícios. Pixels alterados: 14,14%; MAE: 11,21. |

### Diferenças que permanecem

- As imagens ilustrativas são SVGs próprios existentes no projeto, não os ativos originais. Cinco referências quebradas para `/clinic-building-hero.svg` e `/clinic-building-guide.svg` foram corrigidas para o SVG existente `/clinic-operational-hero.svg`; a checagem de carregamento agora torna esse tipo de regressão explícito.
- Os dados de QA não são cópias dos valores dos PNGs. As diferenças de contagem, datas, registros, estado vazio e conteúdo estão discriminadas por rota acima e não foram ocultadas com máscaras.
- Os estados de cobrança real, envio Resend e webhook público não foram homologados: não há credenciais sandbox/providers nem endpoint HTTPS público neste ambiente. Os testes correspondentes usam os mocks existentes.
- As comparações registram diferenças de pixels entre 7,84% e 16,04% no limiar RGB L1=36. Isso inclui conteúdo/data, texto e renderização, não isola apenas geometria. Não se declara identidade pixel a pixel nem paridade visual sem resíduos.

## Correções aplicadas nesta continuação

- Corrigida a especificidade do seletor de pesquisa de especialidades; DOM final mede 40 px em ambos os campos e 0 px de desalinhamento vertical.
- Corrigido o valor do `Select` de tamanho de página e agrupados os controles de paginação para quebrar corretamente em 320 px.
- Corrigida a checagem da prévia de próximos atendimentos do dashboard para não contar linhas de outros painéis.
- Corrigidas cinco referências a SVGs inexistentes; o runner espera carregamento e valida dimensões naturais de todas as imagens.
- Ampliada a arte dos cabeçalhos ilustrados com ações no espaço disponível. A altura do conteúdo permanece estável e a regra responsiva restaura o tamanho relativo em tablet/mobile.
- Compactada a lista de próximos atendimentos; o rodapé do dashboard termina em Y=880,8 px no viewport 1768×890 e permanece dentro da captura.
- Removida uma regra de margem negativa sem componente correspondente.

## Responsividade, acessibilidade e funcionamento

As seis larguras foram exercitadas em todas as rotas. As capturas finais confirmaram URL/título esperado, imagens carregadas e ausência de overflow horizontal. A execução de Chromium (`qa_browser/prescription_browser.py` e `qa_browser/admin_agenda_browser.py`) cobre foco, teclado e Escape em diálogos, ações de agenda, autorização, cadastro, busca, paginação, marcação e responsividade.

Permanecem os limites do estado funcional real documentados acima. A captura não altera dados clínicos para coincidir com os PNGs e o runner de rota não substitui os testes de autorização/fluxo.

## Testes e gates

| Verificação | Resultado final |
|---|---|
| `pytest -q` em PostgreSQL descartável limpo `vitta_one_visual_tests_20261120` | **569 passed, 3 skipped**, 1 aviso de depreciação `StarletteDeprecationWarning` relacionado a `httpx` no `TestClient` |
| `pytest qa_browser/prescription_browser.py qa_browser/admin_agenda_browser.py -q` em banco QA isolado | **42 passed**; inclui fluxo clínico/administrativo e foco/teclado |
| `python -m qa_browser.capture_operational_reference_screens` após o CSS final | **96/96 PASS**, imagens carregadas, comparações refeitas |
| Auditoria de viewport equivalente a zoom 200% | **16/16 PASS** em 884×445 |
| `reflex compile --dry` com o ambiente PostgreSQL QA isolado | **PASS**, compilado em 7,348 s; há avisos preexistentes de depreciação Reflex e assinaturas de `on_submit` |
| OpenSpec strict | **34 passed, 0 failed**, 1 nota informativa sobre target spec arquivada de `patient-portal` |
| `git diff --check` | **PASS** |
| Migrations do banco descartável | `alembic upgrade head` passou até `f031a5aa5002`; nenhuma migration nova nesta change |

Uma execução anterior de Pytest contra um banco compartilhado com os fixtures visuais encontrou colisões de CPF e estado mutado por fluxo de navegador. A suíte completa foi então repetida num banco PostgreSQL limpo e isolado, com os resultados aprovados acima. Nenhum banco/container preexistente ou de produção foi alterado; as bases e contas QA são descartáveis/sintéticas.

## Limitações e próximos passos de revisão

A PR contém o código, relatório e manifesto sanitizado; os PNGs de referência, capturas, overlays e diffs estão fora do Git em `qa-artifacts/operational-reference/`. A CI da PR deve confirmar os gates do repositório após a publicação. Não há migration de produção, deploy ou merge nesta execução.
