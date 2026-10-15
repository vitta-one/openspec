# Revisão visual — Recepção: Operação do Dia

## Referência e captura

A revisão compara a referência anexada **02.01 — Operação do Dia** (1288 × 741 px) com a captura Chromium produzida no [workflow de QA 83](https://github.com/vitta-one/openspec/actions/runs/38670475095). A captura desktop usa viewport de 1280 px; as telas de 1264, 1200, 768, 375 e 320 px verificam os limites entre desktop, tablet e celular.

## Resultado

- A página mantém o título e a data da operação em destaque, seguida pela busca, filtro de profissional, ações de Agenda e a tabela com horário, paciente/telefone, profissional, especialidades, status e ações.
- O painel usa as fontes e tokens de tipografia já definidos pelo produto. Os novos campos herdam a fonte atual; nenhum token ou família tipográfica global foi alterado.
- O espaçamento interno da tabela, cabeçalho, toolbar e paginação dá separação clara entre controles e linhas sem introduzir cartões excessivamente compactos.
- A tabela usa consultas persistidas no dia local da clínica, conserva cancelamentos visíveis e mostra paginação real. A busca global localiza apenas identidade e encaminha para o cadastro do paciente.
- Em 768, 375 e 320 px, a tabela rola dentro da região nomeada; a página não ganha rolagem horizontal. Os horários permanecem em uma linha e os controles empilham sem lacunas verticais exageradas.
- Em 1200 e 1264 px, a toolbar muda para linhas empilhadas quando o espaço não comporta filtros e ações lado a lado. Em 1280 px, os controles ficam alinhados sem cortar o filtro.

## Ajustes encontrados durante a revisão

1. A primeira captura mostrou que bases flexíveis de largura viravam alturas grandes no layout em coluna. As bases foram removidas para telas estreitas, os botões passaram a ocupar a altura natural e a ação de atualização fica compacta no desktop.
2. A coluna de horário quebrava o valor em telas estreitas. A coluna agora mantém horários numa linha e a rolagem fica contida na tabela.
3. A captura de desktop mostrou texto truncado no filtro e na busca. O ponto de mudança da toolbar foi ajustado e o texto auxiliar foi encurtado; o rótulo acessível continua descrevendo busca por nome, telefone ou CPF.

Os screenshots gerados pelo workflow estão no artefato `prescription-qa-visual-evidence`. Os registros usados para exercitar a tabela são sintéticos e existem somente no banco descartável do GitHub Actions.
