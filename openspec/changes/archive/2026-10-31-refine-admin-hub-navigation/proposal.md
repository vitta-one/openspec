## Why

A central `/admin` apresenta listas de ações em superfícies aninhadas, amplas e pouco densas. A sidebar mistura ferramentas locais de inspeção de QA com rotas administrativas reais e deixa de listar destinos existentes. Essa apresentação confunde navegação com permissão e prejudica o uso por teclado e em telas menores.

## What Changes

- Central administrativa passa a reunir cinco destinos reais em dois grupos compactos, com links integrais e largura limitada.
- O atalho "Criar funcionário" abre o cadastro existente em `/admin/funcionarios/novo`.
- A sidebar exibe as seis rotas administrativas já implementadas, com seleção coerente por página.
- Ferramentas QA permanecem condicionadas à flag autorizada, agrupadas em seção separada com caráter de inspeção somente leitura.
- Navegação móvel mantém controle acessível de fechamento dentro da sidebar; controles hamburger expõem estado e destino.
- Corrige descrição da página de configurações para refletir sua capacidade atual somente leitura.

## Impact

- Camada de apresentação Reflex `vitta_one/ui/`, estilos em `assets/styles.css` e testes de rotas/menus.
- Nenhuma migration, novo endpoint, alteração de RBAC ou integração externa.
- A condição de QA e a autorização de cada rota continuam aplicadas no servidor.

## Out of Scope

- Criar configurações editáveis, dashboards/métricas, novos módulos ou permissões.
- Fazer merge/deploy, alterar banco de dados ou dados clínicos.
- Substituir a tecnologia Reflex.
