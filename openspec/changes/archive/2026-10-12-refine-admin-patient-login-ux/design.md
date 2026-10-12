## Context

O Vitta-One usa Reflex 0.9.x, Radix Themes via componentes `rx.*`, PostgreSQL e RBAC server-side. O diretório administrativo já possui handlers completos de criação/edição/ativação de profissionais e especialidades; a change não deve duplicar serviços nem alterar domínio. O preview local do Administrador é explicitamente controlado por `VITTA_ONE_LOCAL_ADMIN_PREVIEW=true` e é somente leitura fora das operações administrativas reais.

A identidade visual e tokens continuam definidos em `DESIGN.md` e `assets/styles.css`. Esta change altera comportamento e composição, não a paleta.

## Goals / Non-Goals

### Goals

- reduzir ruído no diretório administrativo usando diálogos modais para formulários complexos;
- manter listas e estado do diretório visíveis como foco principal;
- tornar o preview de Pacientes escaneável, paginado e com seleção explícita;
- preservar a distinção entre visualização local de QA e permissões reais;
- melhorar o login em largura/altura reduzidas e corrigir o alinhamento do controle de senha;
- manter acessibilidade WCAG 2.2 AA como alvo, foco visível, teclado e reduced motion.

### Non-Goals

- criar novas mutações de paciente/fila;
- introduzir paginação de banco para os fluxos de produção;
- alterar modelos, migrations, serviços de domínio ou roles;
- alterar identidade visual.

## Decisions

### 1. Diálogos administrativos são controlados pelo State

`AdminDirectoryState` ganhará flags explícitas para os diálogos de especialidade e profissional. Abertura, cancelamento e conclusão bem-sucedida serão eventos do State.

Motivos:
- permite abrir create/edit a partir de diferentes ações sem duplicar markup;
- mantém o formulário atual como owner canônico;
- garante que erro server-side preserve valores e mantenha o diálogo aberto;
- fechamento após sucesso evita falsa confirmação antes do commit.

O componente usará `rx.dialog.root(open=..., on_open_change=...)`, `rx.dialog.content`, `rx.dialog.title` e `rx.dialog.description`. O foco/trap/Escape/restauração ficam sob o primitive Radix/Reflex.

### 2. Um formulário reutilizável por entidade

Especialidade usará um único diálogo para criar ou editar. Profissional também reutilizará o formulário existente para create/edit.

A lista continua exibindo Editar/Desativar/Reativar. O botão de topo abre o modo create. Ações de edição preenchem o State e abrem o mesmo diálogo.

### 3. Pacientes usa seleção simples por checkbox

O pedido visual exige checkbox, mas o fluxo atual trabalha com um paciente contextual por vez. Portanto:
- cada linha possui checkbox controlado;
- marcar uma linha substitui qualquer seleção anterior;
- desmarcar a linha selecionada limpa a seleção;
- a seleção é limpa se busca/paginação tornar o paciente selecionado fora do conjunto filtrado somente quando necessário para evitar contexto invisível;
- não existe seleção em massa nesta change.

Essa decisão evita semântica de bulk actions que o backend não suporta.

### 4. Paginação é local ao preview QA

`AdminPreviewState` já carrega somente dados persistidos após autorização. A change mantém essa leitura e pagina o conjunto filtrado em memória, com page size fixo e contagem real.

Motivos:
- a tela alterada é o preview local de QA, não a consulta operacional da Recepção;
- não aumenta escopo de serviço/DB;
- elimina render-all sem fingir paginação remota.

Busca redefine a página para 1. Controles Anterior/Próxima são desabilitados nos limites e o texto informa página atual e total.

### 5. Barra contextual somente leitura

Quando existe paciente selecionado, a UI mostra nome/CPF e ações reais do preview:
- `Ver histórico`: mantém/exibe o painel de histórico operacional existente;
- `Limpar seleção`: remove o contexto selecionado.

Nenhum botão de Recepção/Médico será exposto ao Admin.

### 6. Login responsivo prioriza tarefa

Desktop amplo mantém o split visual. Em largura intermediária, a coluna de formulário ganha proporção suficiente e o painel visual reduz. Em telas estreitas, o visual é ocultado e o formulário ocupa a viewport. Em alturas reduzidas, a coluna de formulário passa a rolar naturalmente e os espaçamentos/headline são compactados.

O botão de senha mantém posição absoluta, mas recebe box de tamanho fixo, `display:grid` e `place-items:center`, garantindo centralização do ícone.

## Risks / Trade-offs

- Paginação local não reduz volume de consulta ao banco; aceitável por ser preview local de QA. Uma futura tela operacional de pacientes pode exigir paginação server-side.
- Diálogos dependem da implementação de foco do primitive Reflex/Radix; compile e validação manual continuam necessários.
- Seleção por checkbox com cardinalidade máxima 1 é menos comum que radio. O pedido explícito do fluxo e a presença de ações contextuais justificam a escolha; o comportamento será anunciado pela UI como “1 paciente por vez”.

## Verification

- validar OpenSpec;
- `python -m pytest -q`;
- `reflex compile --dry`;
- validar abertura/cancelamento/sucesso/erro dos dois diálogos;
- validar busca, no-results, paginação, limites, seleção/desseleção e histórico;
- validar login em desktop amplo, tablet, mobile e viewport de baixa altura;
- validar teclado, Escape do diálogo, foco visível, controle de senha e reduced motion.
