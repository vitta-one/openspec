---
version: alpha
name: "Vitta-One"
description: "Estação clínica interna de alta confiança: precisa, calma, operacional e fiel à identidade visual Vitta-One."
colors:
  canvas: "#F7F8FC"
  surface: "#FFFFFF"
  surface-muted: "#F1F5F9"
  surface-subtle: "#F8FAFC"
  primary: "#0F766E"
  primary-hover: "#0B655F"
  primary-soft: "#E8F5F3"
  text: "#0F172A"
  text-muted: "#475569"
  text-subtle: "#64748B"
  border: "#E2E8F0"
  border-strong: "#CBD5E1"
  info: "#0369A1"
  info-soft: "#F0F9FF"
  warning: "#D97706"
  warning-soft: "#FFFBEB"
  danger: "#E11D48"
  danger-soft: "#FFF1F2"
  success: "#059669"
  success-soft: "#ECFDF5"
  focus: "#0F766E"
  scroll-thumb: "#94A3B8"
  scroll-track: "#F1F5F9"
typography:
  display:
    fontFamily: '"Segoe UI Variable Display", "SF Pro Display", "Segoe UI", system-ui, sans-serif'
    fontSize: "2rem"
    lineHeight: "1.12"
  sans:
    fontFamily: '"Inter", "Segoe UI Variable Text", "Segoe UI", system-ui, sans-serif'
    fontSize: "1rem"
    lineHeight: "1.5"
  utility:
    fontFamily: '"Inter", "Segoe UI Variable Text", "Segoe UI", system-ui, sans-serif'
    fontSize: "0.75rem"
    lineHeight: "1.35"
rounded:
  control: "0.625rem"
  panel: "0.875rem"
  large: "1.125rem"
spacing:
  page-horizontal: "1.75rem"
  page-max: "90rem"
  sidebar-width: "15.5rem"
  rhythm: "0.5rem"
components:
  button: {}
  input: {}
  panel: {}
  alert: {}
  nav-item: {}
  status-badge: {}
  metric-card: {}
  data-row: {}
  scrollbar: {}
---

# Vitta-One Design System

## Overview

### Creative North Star

O Vitta-One deve parecer uma **estação clínica de comando silenciosa**: uma interface que a equipe consegue usar por horas, em ritmo operacional, sem parecer um prontuário legado nem um SaaS decorativo. A identidade parte da marca oficial fornecida ao projeto: teal clínico `#0F766E`, navy `#0F172A` e slate `#475569`.

A assinatura visual é a combinação de **sidebar clínica persistente + cabeçalho operacional compacto + superfícies brancas extremamente alinhadas**. O login concentra a expressão visual da marca por meio de uma geometria médica de grande escala; as telas internas priorizam leitura e operação.

### Product context and register

- **Audiência:** Administrador, Recepcionista, Médico e Financeiro em ambiente interno de clínica.
- **Uso:** desktop como prioridade operacional; tablet e telas estreitas preservam as tarefas essenciais.
- **Idioma:** português brasileiro.
- **Registro:** produto interno, não marketing.
- **Acessibilidade:** WCAG 2.2 AA como alvo.
- **Anti-references:** glassmorphism, gradientes promocionais, sombras pesadas, cards superdimensionados, métricas fictícias, ícones ornamentais e ações que não existem no backend.
- **Token ownership:** `assets/styles.css` é a fonte runtime canônica; este arquivo espelha e explica os valores duráveis aceitos.

### Modo local do Administrador

O Administrador de desenvolvimento pode receber uma navegação unificada somente quando `VITTA_ONE_LOCAL_ADMIN_PREVIEW=true`. Esse modo existe para inspeção visual e QA local. Ele não altera o RBAC de produção nem transforma o Administrador em superusuário de negócio. Áreas ainda não implementadas renderizam estados vazios honestos; Agenda e outras capabilities implementadas usam projeções somente leitura de dados persistidos.

## Colors

A base é fria e discreta para reduzir fadiga. O canvas `#F7F8FC` separa a página das superfícies `#FFFFFF` por contraste e bordas finas, não por efeitos chamativos. Teal é reservado para foco, seleção e ação primária; navy é reservado à informação principal.

Semântica operacional:

- **Informação / Agendada:** `#0369A1` sobre `#F0F9FF`.
- **Chegada confirmada / Na fila:** teal primário `#0F766E` sobre `#E8F5F3`.
- **Atenção / Em andamento:** `#D97706` sobre `#FFFBEB`.
- **Sucesso / Concluída:** `#059669` sobre `#ECFDF5`.
- **Perigo / Cancelada, falha ou ação destrutiva:** `#E11D48` sobre `#FFF1F2`.

Cor nunca é o único sinal de estado; badges mantêm rótulo textual.

## Typography

Títulos usam a pilha de display do sistema com peso forte e tracking levemente negativo. Corpo, listas, tabelas e controles usam uma pilha legível de UI, priorizando Inter quando disponível e caindo para Segoe/system-ui sem download externo.

Horários, contadores e identificadores usam numerais tabulares quando o alinhamento melhora a leitura operacional.

## Layout

- Desktop: sidebar de `15.5rem`, topbar compacto e conteúdo de até `90rem`.
- Tablet: sidebar vira faixa superior rolável; conteúdo mantém leitura em uma ou duas áreas.
- Mobile: login e fluxos operacionais retornam a uma coluna.
- O documento permanece dono da rolagem principal. Tabelas/listas recebem overflow próprio somente quando necessário.
- Cards agrupam comportamento real; não são usados para decorar espaço vazio.

## Elevation & Depth

A hierarquia vem primeiro de borda, espaço e contraste. Sombras são discretas:

- superfícies normais: borda `#E2E8F0` e sombra quase imperceptível;
- menus/drawers futuros: sombra média somente quando flutuarem;
- login: contraste estrutural entre formulário e plano teal.

## Shapes

- controles: `0.625rem`;
- painéis: `0.875rem`;
- contêineres principais: `1.125rem`;
- pill é reservado a estado ou metadado curto.

## Components

### Marca

A logo oficial fornecida ao projeto é a identidade principal do login e shell autenticado. A antiga marca textual `V1` deixa de ser a assinatura principal.

### Login

- layout dividido no desktop;
- formulário objetivo, logo real, status de ambiente e cópia curta;
- painel teal usa geometria médica em grande escala como assinatura visual;
- senha inicia mascarada;
- revelar/ocultar usa botão de ícone `eye` / `eye-off`, com nome acessível e estado pressionado;
- não há links falsos de cadastro ou recuperação enquanto esses fluxos não existem;
- falhas aparecem inline.

### Navegação

A sidebar agrupa os módulos por função reconhecível: Recepção, Agenda, Atendimento clínico, Pacientes, Financeiro e Administração. Em produção, cada role continua vendo apenas o destino compatível. A navegação completa do Administrador existe somente no modo local de QA e é rotulada como tal.

### Topbar

Mostra estado do sistema, identidade atual e role. Não exibe busca global, unidade física, notificações ou métricas sem backend correspondente.

### Forms

- label sempre visível;
- validação pertence ao app, não a balões nativos do navegador;
- inputs preservam geometria em loading/erro;
- textareas operacionais curtas usam `resize: none`;
- a variante de texto clínico longo usa `resize: vertical`, altura inicial confortável e limite de altura para não quebrar a página;
- Select reutiliza o owner acessível Reflex/Radix do projeto;
- ações destrutivas permanecem separadas das primárias.

### Documentos clínicos imprimíveis

A Prescrição imprimível é uma superfície documental, não um segundo shell da aplicação:

- usa fundo branco, largura de leitura controlada e hierarquia tipográfica sóbria;
- mantém logo Vitta-One, identificação do paciente/profissional e itens em fluxo vertical;
- evita cartões decorativos, sidebar, topbar e navegação no papel;
- controles de voltar/imprimir existem apenas na tela e desaparecem em `@media print`;
- blocos de item, observações e aviso de assinatura evitam quebra interna quando possível;
- ausência de assinatura digital é comunicada em texto, nunca por inferência visual.

### Iconography

Ícones Lucide via `rx.icon` são permitidos quando comunicam função reconhecível. Ícone nunca substitui texto na navegação principal. Controles somente de ícone recebem nome acessível.

### Motion

Transições de 120–180ms somente em hover, foco e seleção. Sem animação ambiente. `prefers-reduced-motion` remove movimento não essencial.

### Content and data visualization

Nunca preencher dashboard, histórico clínico ou financeiro com conteúdo de demonstração apresentado como real. Agenda usa slots/Consultas persistidos; Atendimento, Prescrições e histórico usam somente registros persistidos. Projeções locais usam dados reais; módulos futuros mostram estados vazios claros. Prioridade clínica é sempre acompanhada por texto e nunca é inferida pela interface.

## Do's and Don'ts

- **Do:** usar a marca real e a paleta extraída dela.
- **Do:** manter o Admin local como recurso explícito de desenvolvimento, nunca como bypass silencioso.
- **Do:** exibir módulos futuros como estados vazios honestos.
- **Do:** preservar operações reais de pacientes, fila e diretório onde já existem.
- **Do:** manter foco visível, targets confortáveis e estados disabled/busy coerentes.
- **Don't:** adicionar links ou botões sem ação real.
- **Don't:** inventar horários, históricos, diagnósticos ou valores.
- **Don't:** comunicar prioridade apenas por cor.
- **Don't:** esconder scrollbars por estética.
