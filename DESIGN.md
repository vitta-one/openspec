---
version: alpha
name: "Vitta-One"
description: "Interface clínica interna, calma e operacional, com foco em identidade, autorização, diretórios administrativos, fila de atendimento e legibilidade."
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
  success: "#236449"
  success-soft: "#E7F4ED"
  success-border: "#ADD6C2"
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
  queue-row: {}
  priority-badge: {}
  directory-row: {}
  status-badge: {}
  checkbox-group: {}
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

O canvas usa `canvas`, com painéis `surface` e áreas secundárias `surface-muted`. `primary` identifica ação, acesso autorizado e foco institucional. `danger` é reservado a erros e ações de retirada; `success` comunica confirmações concluídas. Texto normal usa `text`; `text-muted` é permitido para informação secundária, mantendo contraste WCAG AA sobre as superfícies atuais. O foco de teclado usa `focus` de forma explícita e não depende apenas de mudança de cor. Prioridades da fila podem usar vermelho, amarelo e verde como reforço semântico, mas sempre acompanhadas pelo rótulo textual correspondente.

## Typography

A fonte é a pilha do sistema para evitar dependência externa e reduzir deslocamento de layout. Títulos usam peso alto e tracking ligeiramente negativo; corpo e controles permanecem em sentence case. Cópia da interface é direta, em português brasileiro e sem jargão técnico quando o usuário não precisa dele.

## Layout

O login adota dois painéis apenas em telas médias ou maiores; no mobile eles empilham verticalmente sem perder a ordem do formulário. Áreas protegidas usam largura máxima de `72rem`, padding horizontal de `1.25rem` e fluxo natural da página. Nos fluxos de Recepção, identidade do paciente e entrada na fila podem ocupar duas colunas apenas quando houver largura suficiente; em telas estreitas voltam para uma coluna mantendo a sequência operacional. A fila permanece uma lista vertical, porque prioridade, relato e ações precisam continuar legíveis sem rolagem horizontal. No painel Administrador, especialidades e formulário de profissional podem dividir a largura apenas em telas amplas; listas continuam verticais e retornam a uma coluna em telas estreitas. Não há sidebar nesta fase.

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

Os destinos autenticados continuam separados por role. Financeiro permanece shell; Administrador hospeda a gestão de profissionais/especialidades e Recepção/Médico hospedam a capability de fila sem criar navegação global nova. A fila ativa é exibida como lista vertical ordenada pelo servidor. Cada item mostra nome, horário de entrada, prioridade textual e relato; ações são botões explícitos. A rota incompatível mantém estado 403 próprio e retorno ao painel autorizado.

### Forms and overlays

Campos possuem label explícita, sem placeholder como substituto de rótulo. E-mail usa semântica `email`/`username`; senha usa `current-password` e alternância acessível de visibilidade. CPF e relato da fila recebem validação no servidor mesmo quando o navegador já aplica restrições básicas. Prioridade usa Select acessível do próprio Reflex/Radix e nunca é inferida pelo sistema. Seleção de múltiplas especialidades usa checkboxes visíveis; vínculo histórico inativo permanece marcado e bloqueado para não ser removido acidentalmente. Reavaliação, retirada e edições administrativas acontecem inline no fluxo para preservar contexto; retirada exige motivo e confirmação explícita, mas não usa modal porque não apaga o histórico. Falhas aparecem em alert inline seguro e confirmações em região `status`. Não existe cadastro público.

### Iconography

Nenhuma biblioteca de ícones é necessária nesta fase. A interface usa texto para ações relevantes; não introduzir dependência apenas para ornamentação.

### Motion

Apenas transições curtas de foco/hover. Nenhuma animação ambiente. Em `prefers-reduced-motion`, transições e animações não essenciais são efetivamente removidas.

### Content and data visualization

A voz é objetiva e operacional. Não exibir métricas ou gráficos simulados. O painel Médico pode mostrar apenas a contagem real de pacientes aguardando e o atendimento ativo da própria identidade. O painel Administrador mostra somente dados persistidos do diretório, incluindo estados ativo/inativo e vínculo opcional com conta Médica. Prioridade é apresentada como dado recebido pela operação, nunca como diagnóstico, recomendação ou cálculo do Vitta-One. Estados vazios devem dizer claramente que não há pacientes aplicáveis sem preencher a interface com conteúdo fictício.

## Do's and Don'ts

- **Do:** usar o teal como sinal consistente de ação, foco e autorização.
- **Do:** manter autorização real no backend e tratar ocultação visual apenas como UX.
- **Don't:** antecipar módulos, métricas ou navegação ainda não especificados pelo OpenSpec.
- **Do:** manter prioridade sempre acompanhada de texto e preservar a ordem recebida do servidor.
- **Do:** comunicar estados ativo/inativo por texto e preservar vínculos históricos durante edições administrativas.
- **Don't:** sugerir que cor, tempo de espera ou interface calculam gravidade clínica.
- **Don't:** reduzir contraste, remover foco ou esconder scrollbar para ganhar aparência “clean”.
