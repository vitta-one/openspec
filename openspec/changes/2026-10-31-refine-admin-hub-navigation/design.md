## Decisão de interface

A página `/admin` permanece um hub de tarefas, sem KPIs. O cabeçalho canônico `page_header` é reutilizado e o conteúdo recebe largura máxima de 70rem. Os grupos "Equipe e acessos" e "Agenda e clínica" usam listas de links em superfície única, com divisórias, ícones alinhados, foco visível e alvos com altura mínima adequada.

Em desktop, os dois grupos compartilham um grid de duas colunas; abaixo de 800px, uma coluna evita truncamento e overflow. O CSS aproveita exclusivamente os tokens existentes e respeita `prefers-reduced-motion`.

## Separação de privilégios

`_ADMIN_TASK_NAV` contém apenas destinos operacionais já registrados no servidor. `_ADMIN_PREVIEW_NAV` contém apenas rotas da inspeção local QA, mostradas separadamente sob `AuthState.local_admin_preview`. A UI não concede acesso: `AuthState`, `verified_path` e guards server-side continuam como fronteiras obrigatórias. Não ampliar permissões de administradores sobre operações clínicas.

## Navegação e estados

O submenu real e o hub convergem para URLs existentes; páginas de profissionais, especialidades e configurações recebem chaves de navegação ativas próprias. O hamburger informa `aria-expanded` e `aria-controls`; o drawer móvel oferece botão explícito de fechamento, além do scrim e fechamento ao navegar.

## Riscos e validação

- Confirmar em navegador foco, fechamento e retorno de foco do drawer (incluindo Escape) antes da aprovação final.
- Verificar que o modo QA não é habilitado fora de ambiente autorizado, além da flag atual.
- Testar em 320, 390, 768, 1024 e 1440px e verificar rotas, RBAC e contrastes.
- Não declarar os testes de browser concluídos sem evidência.

O recurso móvel recebe aprimoramento progressivo sem dependência externa: script local aplica foco inicial ao botão de fechar, contém Tab no drawer aberto, aciona o fechamento via botão Reflex em Escape e devolve foco ao hamburger quando disponível.
