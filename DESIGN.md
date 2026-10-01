---
version: alpha
name: "Vitta-One — Clinical Precision & Calm"
description: "Sistema clínico interno de alta confiança, com navegação operacional direta, superfícies calmas e identidade teal própria."
colors:
  canvas: "#F7F8FC"
  surface: "#FFFFFF"
  surface-muted: "#F1F4FB"
  surface-strong: "#E8EDF8"
  primary: "#00645D"
  primary-hover: "#004F4A"
  primary-soft: "#E2F2EF"
  secondary: "#0A6EA8"
  text: "#111827"
  text-muted: "#556070"
  text-subtle: "#7A8492"
  border: "#DDE3EC"
  danger: "#B42318"
  danger-soft: "#FFF2F0"
  success: "#176B52"
  success-soft: "#E9F7F1"
  focus: "#0B7D74"
  scroll-thumb: "#9AA8B8"
  scroll-track: "#EEF2F6"
typography:
  display:
    fontFamily: "Plus Jakarta Sans, Segoe UI, sans-serif"
  sans:
    fontFamily: "Inter, Segoe UI, sans-serif"
rounded:
  control: "0.72rem"
  panel: "1rem"
  shell: "1.35rem"
spacing:
  page-horizontal: "2.25rem"
  page-max: "76rem"
  sidebar: "15.5rem"
components:
  login: {}
  sidebar: {}
  topbar: {}
  panel: {}
  button: {}
  input: {}
  feedback: {}
  module-card: {}
---

# Vitta-One Design System

## Overview

### North Star

O Vitta-One deve parecer uma **estação de trabalho clínica de alta confiança**, não uma landing page de saúde nem um dashboard genérico de SaaS. A referência visual aprovada combina os mockups enviados pelo produto com uma linguagem própria: navegação lateral compacta, teal clínico profundo, superfícies quase brancas levemente azuladas, hierarquia tipográfica forte e pouca ornamentação.

### Assinatura visual

A identidade memorável é a combinação entre a **logo Vitta-One real**, o teal operacional e o contraste entre superfícies brancas e canvas frio. No login, a fotografia médica ocupa uma única área expressiva; dentro do produto, a interface volta a ser contida e funcional.

### Anti-references

- não usar glassmorphism, gradientes decorativos ou cards excessivamente flutuantes;
- não simular métricas, pacientes, consultas ou dados clínicos para preencher espaço;
- não usar azul hospitalar genérico como cor principal;
- não esconder ações importantes em ícones sem nome acessível;
- não criar telas diferentes para a mesma operação quando um primitivo compartilhado resolve.

## Colors

`primary` representa ação, foco e navegação selecionada. `secondary` é reservado a informação operacional complementar. Canvas e superfícies possuem contraste baixo o bastante para uso prolongado, mas bordas permanecem visíveis. Estados de erro/sucesso usam semântica própria e sempre acompanham texto.

## Typography

`Plus Jakarta Sans` é usada para títulos e momentos de identidade. `Inter` é a fonte operacional para corpo, formulários, listas e metadados. O fallback mantém `Segoe UI` para Windows. Títulos usam tracking negativo discreto; labels operacionais usam peso 600–700 sem caixa alta extensa, exceto eyebrows curtos.

## Layout

O produto autenticado usa sidebar fixa de `15.5rem` em desktop e navegação horizontal rolável em telas estreitas. O conteúdo possui largura máxima de `76rem`, enquanto o topbar permanece compacto e contextual. A página deve rolar naturalmente; painéis internos só assumem scroll quando o conteúdo exigir de fato.

O login usa duas zonas: formulário objetivo e uma única imagem clínica com legenda curta. Em mobile, o formulário vem primeiro e a imagem vira apoio visual abaixo.

## Elevation & Depth

Bordas e contraste de superfície criam a hierarquia principal. Sombras são discretas em cards interativos e mais presentes apenas no shell do login. Não empilhar sombras em formulários, listas ou tabelas.

## Shapes

Controles usam cerca de `0.72rem`; painéis `1rem`; o shell do login `1.35rem`. Pills ficam restritas a status/chips. A logo mantém sua geometria própria e não deve ser redesenhada com CSS.

## Components

### Navigation

Admin vê toda a estrutura de módulos do produto. Roles operacionais veem somente o destino compatível com sua função. A sidebar comunica a seleção com fundo teal + texto branco; segurança continua server-side.

### Authentication

Senha é mascarada por padrão. O controle de visibilidade é um botão de ícone `eye/eye_off`, possui nome acessível dinâmico e não altera o tamanho do campo. Login preserva suporte a password managers, autofill e paste.

### Forms and feedback

Labels são explícitas. Erros aparecem inline em texto e região `alert`; sucesso em região `status`. Botões mantêm dimensão durante loading e bloqueiam envio duplicado. Textareas não são redimensionáveis manualmente e recebem altura inicial suficiente.

### Data and empty states

Dados operacionais só aparecem quando existem no backend. Capabilities futuras usam estado vazio honesto, nunca pacientes, consultas, horários ou valores inventados. A interface pode explicar o próximo fluxo aprovado sem criar falsa affordance.

### Iconography

Usar Lucide via `rx.icon`, tamanho 16–22px na maior parte do produto, stroke regular e sem dependência decorativa adicional. Ícone reforça rótulo; ações críticas não dependem apenas dele.

### Motion

Hover e press usam transições de 120–140ms. `prefers-reduced-motion` efetivamente desativa movimento não essencial.

## Do's and Don'ts

- **Do:** tratar sidebar, feedback, campos e painéis como componentes canônicos compartilhados.
- **Do:** usar a foto médica apenas onde ela dá contexto humano real, principalmente no acesso.
- **Do:** preservar RBAC no servidor mesmo quando o Admin enxerga a arquitetura completa do produto.
- **Do:** usar estados vazios orientados à próxima ação/etapa real.
- **Don't:** preencher Agenda, Financeiro ou Prontuário com dados de demonstração no produto real.
- **Don't:** transformar a sidebar em menu promocional ou colocar ícones ornamentais sem função.
- **Don't:** esconder scrollbar global para ganhar aparência “clean”.
