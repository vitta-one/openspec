# UX Contract — Vitta-One

## Escopo

Contrato de comportamento para autenticação, navegação autenticada e fluxos CRUD já implementados. Regras de negócio continuam nos specs OpenSpec e no backend; este documento registra apenas consequências observáveis de UX.

## Fontes de negócio

- `openspec/specs/access-control/spec.md` — autenticação, sessão, RBAC e 403.
- `openspec/specs/patient-reception-queue/spec.md` — paciente e fila.
- `openspec/specs/professional-specialty-management/spec.md` — diretório administrativo.
- `docs/project-overview.md` e `docs/domain-model.md` — escopo global e capabilities futuras.

## Navegação canônica

- Login bem-sucedido envia o usuário ao `dashboard_path` da role.
- Administrador entra em `/admin` e vê a arquitetura completa de módulos; isso não concede mutações operacionais de Recepção/Médico.
- Roles operacionais veem somente sua navegação relevante.
- Navegação direta para rota incompatível mantém 403 explícito e retorno ao próprio painel.
- Cada rota define título localizado e honesto.

## Autenticação

- E-mail: `autocomplete=username`.
- Senha: `autocomplete=current-password`, mascarada por padrão.
- Mostrar/ocultar senha usa botão de ícone com `aria-label` dinâmico e não altera layout.
- Erro de credencial permanece genérico e inline.
- Durante submit, o botão mantém geometria, bloqueia duplo envio e indica loading.
- Logout revoga a sessão no servidor antes de limpar o cliente.

## Feedback e recuperação

- Erro corrigível: alerta inline próximo ao fluxo que o gerou.
- Sucesso de mutação: status inline canônico.
- Nenhum `alert()`, `confirm()` ou `prompt()` do navegador.
- Estados ainda não implementados são apresentados como indisponíveis/planejados; nunca como dados simulados.

## Formulários

- Labels reais e clicáveis.
- Validação relevante é server-side; UI nunca substitui autorização ou regra de negócio.
- Campos preservam valores após erro sempre que o State atual permitir.
- Textareas usam altura estável e `resize: none`.
- Select existente continua com o primitivo acessível Reflex/Radix.

## Superfícies canônicas

| Capability | Dono canônico | Fonte |
|---|---|---|
| Shell autenticado | `vitta_one/ui/components.py::protected_workspace` | DESIGN + este contrato |
| Sidebar/topbar | `vitta_one/ui/components.py` | DESIGN + este contrato |
| Input/textarea | `assets/styles.css` + helpers UI | DESIGN |
| Feedback | `feedback_region`, `error_banner`, `success_banner` | este contrato |
| Form administrativo | componentes do diretório | OpenSpec professional-specialty-management |
| Fila | componentes `queue_components.py` | OpenSpec patient-reception-queue |

## Responsividade e acessibilidade

- Meta: WCAG 2.2 AA.
- Foco visível sempre presente.
- Sidebar vira navegação horizontal rolável abaixo de 900px; conteúdo nunca fica escondido atrás dela.
- Controle icon-only possui nome acessível e `title` de apoio.
- `prefers-reduced-motion` remove movimento não essencial.
- `forced-colors` mantém foco e seleção navegável.
