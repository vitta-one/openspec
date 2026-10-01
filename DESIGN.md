---
version: alpha
name: "Vitta-One"
description: "Interface clínica interna, calma e operacional, com autenticação premium e um hub visual do Administrador que não altera as fronteiras de autorização do backend."
colors:
  canvas: "#F4F8F7"
  surface: "#FFFFFF"
  surface-muted: "#EAF3F1"
  surface-subtle: "#F9FBFB"
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
  warning: "#80551A"
  warning-soft: "#FFF7E6"
  warning-border: "#E8CEA0"
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
  login: {}
  admin-navigation: {}
  preview-panel: {}
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

A interface se inspira em uma estação de trabalho clínica bem organizada: superfícies claras, contraste alto, sinalização curta e uma única cor institucional para orientar ações e foco. O produto deve transmitir controle e rastreabilidade, não aparência promocional. A referência visual anexada pelo time é tratada como direção de produto — sidebar calma, conteúdo clínico denso porém legível e detalhes contextuais — sem copiar dados fictícios como se fossem produção.

### Product context and register

- **Audience and primary job:** equipe interna da clínica — Administrador, Recepcionista, Médico e Financeiro — acessando somente operações compatíveis com sua função. O Administrador possui ainda um hub visual de revisão das telas futuras; esse hub não concede permissão server-side para operações de outras roles.
- **Target market(s) and evidence:** o projeto acadêmico não fixa um mercado além do contexto de clínica; não inferir requisitos regionais adicionais sem uma change específica.
- **Locale(s) and language policy:** interface e documentação em português brasileiro, conforme `AGENTS.md` e `openspec/config.yaml`.
- **Usage scene:** aplicação web operacional, usada em desktop e também utilizável em telas estreitas; clareza e velocidade de leitura têm prioridade sobre densidade decorativa.
- **Register:** produto interno.
- **Memorable signature:** logotipo oficial Vitta-One fornecido pelo time, com o símbolo circular de cruz usado como marca compacta quando o espaço exigir.
- **Restraint:** autenticação, mensagens de erro, ações e shells protegidos devem permanecer familiares, silenciosos e previsíveis.
- **Anti-references:** landing pages de saúde com gradientes promocionais, excesso de glassmorphism, dashboards que tratem números de demonstração como dados reais e qualquer UI que simule autorização que o backend não concedeu.
- **Token ownership/runtime mapping:** `assets/styles.css` é a fonte runtime canônica desta fase; este arquivo espelha os tokens aceitos e explica sua intenção. Componentes Reflex consomem somente tokens semânticos `--vitta-*` para valores duráveis desta superfície.

## Colors

O canvas usa `canvas`, com painéis `surface`, áreas secundárias `surface-muted` e áreas de leitura `surface-subtle`. `primary` identifica ação, acesso autorizado e foco institucional. `danger` é reservado a erros e ações realmente destrutivas; `warning` comunica risco recuperável ou funcionalidade ainda não liberada; `success` comunica confirmações concluídas. Texto normal usa `text`; `text-muted` é permitido para informação secundária, mantendo contraste WCAG AA sobre as superfícies atuais. O foco de teclado usa `focus` de forma explícita e não depende apenas de mudança de cor. Prioridades da fila podem usar vermelho, amarelo e verde como reforço semântico, sempre acompanhadas pelo rótulo textual correspondente.

## Typography

A fonte é a pilha do sistema para evitar dependência externa e reduzir deslocamento de layout. Títulos usam peso alto e tracking ligeiramente negativo; corpo e controles permanecem em sentence case. Cópia da interface é direta, em português brasileiro e sem jargão técnico quando o usuário não precisa dele.

## Layout

O login usa um painel de formulário objetivo e, em telas médias ou maiores, uma ilustração clínica fornecida pelo time. Em telas estreitas a imagem é removida para priorizar a tarefa de autenticação e eliminar rolagem decorativa. O formulário preserva largura confortável de leitura, labels sempre visíveis e feedback no próprio fluxo.

Áreas protegidas de Recepção, Médico e Financeiro mantêm o shell atual e o fluxo natural da página. O hub do Administrador é uma exceção deliberada e local: em desktop usa sidebar persistente apenas dentro de `/admin`; em telas menores ela se transforma em navegação horizontal rolável, mantendo todas as opções acessíveis sem esconder ações. Isso não cria uma navegação global para as demais roles e não altera a decisão da change de agenda de evoluir `/recepcao` sem novo shell global.

Nos fluxos de Recepção, identidade do paciente e entrada na fila podem ocupar duas colunas apenas quando houver largura suficiente; em telas estreitas voltam para uma coluna mantendo a sequência operacional. A fila permanece lista vertical. No painel Administrador funcional, especialidades e formulário de profissional podem dividir largura apenas em telas amplas; listas retornam a uma coluna em telas estreitas.

## Elevation & Depth

Hierarquia é criada principalmente por superfície, borda e espaçamento. O login, o hero administrativo e cards de módulo podem usar sombra discreta. Controles rotineiros permanecem planos. Não empilhar camadas decorativas ou sombras fortes.

## Shapes

Controles usam raio `0.75rem`; painéis principais usam `1.25rem`. O símbolo oficial da marca pode usar moldura compacta quando necessário. Bordas são funcionais para separar campos e superfícies.

## Components

### Foundational visual states

Todo controle interativo deve ter estado padrão, hover, foco visível, disabled/busy quando aplicável e feedback textual para erro. `prefers-reduced-motion` remove transições não essenciais. `forced-colors` preserva foco operável. Componentes demonstrativos devem declarar visualmente que são prévia e não podem se apresentar como dados clínicos persistidos.

### Buttons and actions

A ação primária usa teal sólido; ações secundárias usam outline/ghost. Botões ocupam a mesma geometria durante loading e ficam desabilitados para evitar envio duplicado. Logout é ação secundária e não destrutiva visualmente. Botões somente de ícone exigem nome acessível localizado.

### Navigation and data display

Os destinos autenticados continuam separados por role. Financeiro permanece shell; Administrador hospeda gestão funcional de profissionais/especialidades e o novo hub visual de revisão. Recepção/Médico continuam nas capabilities já implementadas sem ganhar autorização nova por consequência do redesign.

A sidebar do Administrador navega entre seções visuais dentro de `/admin`. As seções Recepção, Agenda, Atendimento clínico e Pacientes usam conteúdo de demonstração explicitamente rotulado e não chamam operações protegidas de outra role. A seção Administração continua usando dados persistidos e handlers server-side existentes. A rota incompatível mantém estado 403 próprio e retorno ao painel autorizado.

### Forms and overlays

Campos possuem label explícita, sem placeholder como substituto de rótulo. E-mail usa semântica `email`/`username`; senha usa `current-password` e alternância acessível de visibilidade. A alternância usa ícones `eye` / `eye-off`, preserva valor e foco, muda o nome acessível entre “Mostrar senha” e “Ocultar senha” e mantém a senha mascarada por padrão. Formulários de produto usam validação controlada pelo app (`noValidate`) e feedback inline.

CPF e relato da fila recebem validação no servidor mesmo quando o navegador já aplica restrições básicas. Prioridade usa Select acessível do próprio Reflex/Radix e nunca é inferida pelo sistema. Seleção de múltiplas especialidades usa checkboxes visíveis; vínculo histórico inativo permanece marcado e bloqueado para não ser removido acidentalmente. Reavaliação, retirada e edições administrativas preservam contexto. Falhas aparecem em alert inline seguro e confirmações em região `status`. Não existe cadastro público.

### Iconography

Ícones Lucide já expostos pelo próprio Reflex podem ser usados para semântica, orientação e ações compactas; não adicionar nova dependência de ícones apenas para ornamentação. Ícones nunca substituem labels essenciais. Ações somente de ícone, como revelar senha e sair no hub administrativo, precisam de `aria-label` localizado.

### Motion

Apenas transições curtas de foco/hover e deslocamentos mínimos de cards quando isso reforçar interação. Nenhuma animação ambiente. Em `prefers-reduced-motion`, transformações são removidas e transições não essenciais são efetivamente desativadas.

### Content and data visualization

A voz é objetiva e operacional. Não exibir métricas ou gráficos simulados em superfícies que se apresentem como produção. A única exceção desta fase é o hub visual do Administrador: dados ilustrativos podem aparecer quando estiverem inequivocamente marcados como **demonstração/prévia**, sem gravação e sem inferência clínica. O painel Médico continua mostrando somente a contagem real de pacientes aguardando e o atendimento ativo da própria identidade. O painel Administrador funcional mostra somente dados persistidos do diretório. Estados vazios devem dizer claramente que não há dados aplicáveis sem preencher a interface com conteúdo fictício.

## Do's and Don'ts

- **Do:** usar o teal como sinal consistente de ação, foco e autorização.
- **Do:** usar o logotipo oficial fornecido pelo time em superfícies de identidade, preservando proporção e contraste.
- **Do:** manter autorização real no backend e tratar ocultação/preview visual apenas como UX.
- **Do:** rotular dados demonstrativos no hub visual do Administrador e impedir que eles disparem mutações clínicas reais.
- **Don't:** transformar a sidebar do Administrador em autorização implícita para rotas ou operações de outras roles.
- **Don't:** antecipar persistência de prontuário, prescrição, exames, pagamentos ou estados clínicos ainda não especificados pelo OpenSpec.
- **Do:** manter prioridade sempre acompanhada de texto e preservar a ordem recebida do servidor.
- **Do:** comunicar estados ativo/inativo por texto e preservar vínculos históricos durante edições administrativas.
- **Don't:** sugerir que cor, tempo de espera ou interface calculam gravidade clínica.
- **Don't:** reduzir contraste, remover foco ou esconder scrollbar para ganhar aparência “clean”.