# Design — Navegação global

## Componentes
Manter `SidebarState`, `authenticated_sidebar`, `authenticated_topbar` e `protected_workspace`. Não duplicar sidebar nem rotas. Administrador tem dois grupos independentes: visualizações QA (condicionadas à flag local e autorização no servidor) e Administração (visão geral, funcionários, profissionais, especialidades, horários, configurações).

## Atividade da rota
Cada página administrativa fornece uma chave de navegação; páginas de cadastro ou detalhe reutilizam a chave do respectivo destino pai. O item ancestral recebe uma classe visual discreta, nunca `aria-current="page"`. Apenas o destino atual recebe `aria-current="page"`.

## Responsividade
A sidebar continua parte do grid no desktop; recolhida vira trilho de ícones com nomes acessíveis e títulos nativos. Até 1050 px o mesmo elemento `aside` funciona como drawer, com botão de fechar, scrim e sem scroll de fundo. Um script progressivo apenas gerencia foco, Escape, `inert` e `aria-modal` quando aberto, sem executar autorização e sem alterar estado clínico.

## Segurança
Menus refletem a role; `AuthState.load_protected` e loaders de preview seguem como fronteira de autorização no servidor. A flag QA não promove o administrador a médico ou recepcionista.

## Alternativas rejeitadas
Criar segundo componente mobile e renderizar duas navegações; migrar Reflex para React; oferecer rotas de trabalho não implementadas.
