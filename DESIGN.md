---
version: alpha
name: "Vitta-One"
description: "Interface clínica interna, calma e operacional, com foco em identidade, autorização e legibilidade."
colors:
  canvas: "#F4F8F7"
  surface: "#FFFFFF"
  surface-muted: "#EAF3F1"
  primary: "#0B5D56"
  primary-hover: "#084B46"
  primary-soft: "#D8EBE7"
  text: "#18302D"
  text-muted: "#586E6B"
  border: "#CBDAD7"
  border-hover: "#9DB5B1"
  danger: "#A43A3A"
  danger-soft: "#FFF0F0"
  danger-border: "#E7B8B8"
  focus: "#0E7C72"
  scroll-thumb: "#8EA6A2"
  scroll-track: "#EDF3F2"
typography:
  sans:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
rounded:
  control: "0.75rem"
  panel: "1.25rem"
spacing:
  page-horizontal: "1.25rem"
  page-max: "72rem"
components:
  button: {}
  input: {}
  panel: {}
  alert: {}
  scrollbar: {}
---

# Vitta-One Design System

## Overview

### Creative North Star

A interface se inspira em uma estação de trabalho clínica bem organizada: superfícies claras, contraste alto, sinalização curta e uma única cor institucional para orientar ações e foco. O produto deve transmitir controle e rastreabilidade, não aparência promocional.

### Product context and register

- **Audience and primary job:** equipe interna da clínica — Administrador, Recepcionista, Médico e Financeiro — acessando somente a área compatível com sua função.
- **Target market(s) and evidence:** o projeto acadêmico não fixa um mercado além do contexto de clínica; não inferir requisitos regionais adicionais sem uma change específica.
- **Locale(s) and language policy:** interface e documentação em português brasileiro, conforme `AGENTS.md` e `openspec/config.yaml`.
- **Usage scene:** aplicação web operacional, usada em desktop e também utilizável em telas estreitas; clareza e velocidade de leitura têm prioridade sobre densidade decorativa.
- **Register:** produto interno.
- **Memorable signature:** marca compacta `V1` com geometria assimétrica discreta e uma linha clínica horizontal como elemento de orientação.
- **Restraint:** autenticação, mensagens de erro, ações e shells protegidos devem permanecer familiares, silenciosos e previsíveis.
- **Anti-references:** landing pages de saúde com gradientes promocionais, excesso de glassmorphism, métricas fictícias e dashboards preenchidos antes de suas changes de negócio.
- **Token ownership/runtime mapping:** `assets/styles.css` é a fonte runtime canônica desta fase; este arquivo espelha os tokens aceitos e explica sua intenção. Componentes Reflex consomem somente tokens semânticos `--vitta-*` para valores duráveis desta superfície.

## Colors

O canvas usa `canvas`, com painéis `surface` e áreas secundárias `surface-muted`. `primary` identifica ação, acesso autorizado e foco institucional. `danger` é reservado a erros. Texto normal usa `text`; `text-muted` é permitido para informação secundária, mantendo contraste WCAG AA sobre as superfícies atuais. O foco de teclado usa `focus` de forma explícita e não depende apenas de mudança de cor.

## Typography

A fonte é a pilha do sistema para evitar dependência externa e reduzir deslocamento de layout. Títulos usam peso alto e tracking ligeiramente negativo; corpo e controles permanecem em sentence case. Cópia da interface é direta, em português brasileiro e sem jargão técnico quando o usuário não precisa dele.

## Layout

O login adota dois painéis apenas em telas médias ou maiores; no mobile eles empilham verticalmente sem perder a ordem do formulário. Shells protegidos usam largura máxima de `72rem`, padding horizontal de `1.25rem` e fluxo natural da página. Não há sidebar nem grade de módulos nesta change porque esses comportamentos ainda não foram especificados.

## Elevation & Depth

Hierarquia é criada principalmente por superfície, borda e espaçamento. Apenas o painel principal e a marca compacta usam sombra. Não usar sombras em controles rotineiros nem empilhar camadas decorativas.

## Shapes

Controles usam raio `0.75rem`; painéis principais usam `1.25rem`. A marca `V1` é a única exceção assimétrica. Bordas são sempre funcionais para separar campos e superfícies.

## Components

### Foundational visual states

Todo controle interativo deve ter estado padrão, hover, foco visível, disabled/busy quando aplicável e feedback textual para erro. `prefers-reduced-motion` remove transições não essenciais. `forced-colors` preserva foco operável.

### Buttons and actions

A ação primária usa teal sólido; ações secundárias usam outline/ghost. Botões ocupam a mesma geometria durante loading e ficam desabilitados para evitar envio duplicado. Logout é ação secundária e não destrutiva visualmente.

### Navigation and data display

Nesta change não existe navegação de módulos nem dados clínicos. Os quatro destinos autenticados são shells mínimos. A rota incompatível apresenta estado 403 próprio e retorno ao painel autorizado.

### Forms and overlays

Campos possuem label explícita, sem placeholder como substituto de rótulo. E-mail usa semântica `email`/`username`; senha usa `current-password` e alternância acessível de visibilidade. Falha de credenciais aparece em alert inline genérico. Não existe cadastro público.

### Iconography

Nenhuma biblioteca de ícones é necessária nesta fase. A interface usa texto para ações relevantes; não introduzir dependência apenas para ornamentação.

### Motion

Apenas transições curtas de foco/hover. Nenhuma animação ambiente. Em `prefers-reduced-motion`, transições e animações não essenciais são efetivamente removidas.

### Content and data visualization

A voz é objetiva e operacional. Não exibir métricas, gráficos ou dados de negócio simulados. Cada shell deve explicar que as funcionalidades correspondentes serão implementadas em changes próprias.

## Do's and Don'ts

- **Do:** usar o teal como sinal consistente de ação, foco e autorização.
- **Do:** manter autorização real no backend e tratar ocultação visual apenas como UX.
- **Don't:** antecipar módulos, métricas ou navegação ainda não especificados pelo OpenSpec.
- **Don't:** reduzir contraste, remover foco ou esconder scrollbar para ganhar aparência “clean”.
