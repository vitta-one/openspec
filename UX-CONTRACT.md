# UX Contract

## Product context

- Audience: equipe interna da clínica Vitta-One — Administrador, Recepcionista, Médico e Financeiro.
- Primary jobs: autenticar-se com segurança, operar somente o módulo autorizado e executar fluxos clínico-administrativos com feedback claro.
- Target market(s): não definido além do contexto acadêmico de clínica; não inferir requisitos regionais sem fonte de produto.
- Active locales: `pt-BR`.
- Language/content register and native-review policy: português brasileiro objetivo e operacional; copy clínica ou regulatória nova exige revisão da equipe responsável pela change.
- Timezone/calendar policy: agenda futura segue `VITTA_ONE_CLINIC_TIMEZONE` quando a capability `appointment-scheduling` for aplicada; não assumir timezone do navegador/servidor.
- Accessibility target: WCAG 2.2 AA.

## Business-context sources

| Domain / scope | Authoritative source | Source type | Reviewed date |
|---|---|---|---|
| Permission model | `openspec/specs/access-control/spec.md` | OpenSpec consolidado | 2026-09-30 |
| Fila de pacientes | `openspec/specs/patient-reception-queue/spec.md` | OpenSpec consolidado | 2026-09-30 |
| Profissionais/especialidades | `openspec/specs/professional-specialty-management/spec.md` | OpenSpec consolidado | 2026-09-30 |
| Agenda/consulta em planejamento | `openspec/changes/add-appointment-scheduling/` | OpenSpec change ativa | 2026-09-30 |
| Modelo e ciclo clínico | `docs/domain-model.md` | Modelo de domínio | 2026-09-30 |
| Billing / payment | `docs/project-overview.md` + changes futuras | Contexto de projeto | 2026-09-30 |
| Legal / regulatory copy | Não há fonte aprovada nesta fase | — | 2026-09-30 |

## Visual contract

- Project `DESIGN.md`: `DESIGN.md` na raiz.
- Token ownership model: runtime existente continua canônico.
- Runtime design-system/token source: `assets/styles.css` + primitives Reflex/Radix já utilizados.
- Mapping/export/adapters: tokens duráveis entram como `--vitta-*`; `DESIGN.md` espelha os valores aceitos.
- Token drift gate: revisar `DESIGN.md` e `assets/styles.css` juntos em mudanças de sistema; executar lint oficial do DESIGN.md.
- Supported themes: light nesta fase; forced-colors precisa permanecer operável.
- Design-context owner/review policy: mudanças sistêmicas de shell, tokens, identidade ou navegação atualizam `DESIGN.md` no mesmo changeset.

## Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Table Selection | Não utilizado nesta fase | — | page / all-results apenas quando especificado | componente + E2E quando introduzido |
| Select/Listbox | Reflex/Radix Select já usado no projeto | `DESIGN.md` + shared components | authored | teclado + popup |
| Date | Capability futura de agenda | change `add-appointment-scheduling` | native `datetime-local` somente se popup de plataforma for aceito pela change | locale + teclado + E2E |
| Form | helpers compartilhados em `vitta_one/ui/components.py` + states server-side | este contrato + specs da capability | create / edit | validação + erro server-side |
| Scrollbar | baseline global em `assets/styles.css` | `DESIGN.md` | exceções apenas de geometria | estilo computado/browser |
| Toast | Não existe owner nesta fase; feedback crítico permanece inline/status | este contrato | success / warning / info / error quando um provider for criado | live-region |
| CRUD | states/services da capability + feedback compartilhado | specs OpenSpec + sibling flow | inline / return conforme capability | fluxo completo |

## Component behavior

| Component | Default | Hover | Focus | Active | Disabled | Busy | Error |
|---|---|---|---|---|---|---|---|
| Button | label explícita | contraste de superfície | anel `--vitta-focus` | sem deslocamento de layout | sem handler efetivo | geometria estável + spinner/texto | erro no contexto da ação |
| Icon button | ícone semântico + nome acessível | superfície leve | anel visível | estado pressed quando toggle | não acionável | sem troca de largura/altura | erro fora do ícone |
| Input | label visível | borda reforçada | borda + ring | n/a | sem edição | n/a | `aria-invalid` + mensagem existente |
| Secret input | masked | igual a input | foco preservado | botão eye/eye-off | n/a | n/a | erro genérico de login |
| Search | owner ainda não criado | — | — | — | — | — | — |
| Textarea | resize none | borda reforçada | borda + ring | n/a | preserva legibilidade | n/a | texto associado |
| Table/list | estrutura estável | realce sutil quando necessário | alvo interno focável | seleção textual, não só cor | ação indisponível explicada | área preservada | erro/empty/no-results distintos |

## Dataset navigation

- Admin tables: listas atuais são pequenas/bounded; não inventar paginação cliente sobre endpoint incompleto.
- Exploratory lists: não aplicável nesta fase.
- URL state: rotas protegidas são por role; o hub visual do Administrador usa estado local de seção dentro de `/admin` e não representa deep link canônico.
- Page size: não aplicável enquanto listas atuais não forem paginadas.
- Empty/no-results/error/loading treatment: mensagens próprias e região estável; dados de demonstração só em preview explicitamente rotulado.
- Back/scroll restoration: rotas por role deixam o navegador controlar Back; troca de seção visual do Admin não navega para outra role.
- Selection scope: não aplicável nesta fase.

## Flow ledger

| Operation | Trigger | Pending | Success destination | Success feedback | Failure recovery | Focus outcome | Source ref |
|---|---|---|---|---|---|---|---|
| Login | `Entrar no Vitta-One` | botão bloqueado + feedback de validação | dashboard da role | navegação autorizada | banner genérico, sem revelar credencial | formulário/rota destino | `access-control/spec.md` |
| Logout | `Sair` | operação pessimista | `/login` | redirecionamento | erro no shell, sessão preservada se revogação falhar | login | `access-control/spec.md` |
| Criar/editar diretório | verbos específicos do formulário | botão bloqueado | fica no contexto administrativo | região `status` | erro inline + valores seguros preservados | contexto do formulário/lista | `professional-specialty-management/spec.md` |
| Desativar/reativar diretório | ação explícita | mutação pessimista | mesmo contexto | região `status` | erro inline | linha/contexto | `professional-specialty-management/spec.md` |
| Retirar da fila | ação explícita + motivo | mutação pessimista | fila atualizada | região `status` | erro inline, histórico preservado | contexto da fila | `patient-reception-queue/spec.md` |
| Navegar no preview Admin | item da sidebar/mobile nav | imediato/local | mesma rota `/admin` | seleção visual | voltar à Visão geral | seção escolhida | decisão visual 2026-09-30 |

## Navigation and responsive behavior

- Route document title policy: `{Página} | Vitta-One`, já configurado no registro de páginas Reflex; 403 possui título próprio.
- Route error / 403 page behavior: usuário autenticado sem role exigida recebe página 403 própria e retorno ao dashboard autorizado; nunca transformar em 404/login falso.
- Breadcrumb/tab/route-state policy: abas são somente para vistas pares dentro do mesmo contexto; o preview de paciente usa tabs locais e não finge rotas públicas.
- Sidebar/drawer/bottom-sheet transformation: sidebar existe apenas no hub `/admin`; abaixo do breakpoint vira navegação horizontal rolável com os mesmos itens e nomes acessíveis.
- Responsive table strategy: listas operacionais empilham ou preservam leitura sem esconder ações; tabelas futuras escolhem estratégia conforme comparação necessária.
- Truncation/full-value access: informações essenciais quebram linha; não esconder valor clínico necessário em ellipsis sem acesso alternativo.
- Focus restoration and sticky-obstruction policy: foco visível; topbar/nav sticky não podem encobrir alvo focado; usar scroll padding/margin quando necessário.

## Overlays and feedback

- Dialog primitive: usar Reflex/Radix somente quando modal for de fato necessário; nenhum browser `alert/confirm/prompt`.
- Destructive confirmation levels: desativação/retirada recuperável usa warning/explicação; hard-delete futuro exige danger explícito e fonte de domínio.
- Toast placement/duration/deduplication: não existe provider nesta fase; não criar toast screen-local.
- Alert/banner scope and persistence: erro de formulário/página permanece inline até correção; preview usa banner persistente para declarar dados demonstrativos.
- Tooltip delay/dismissal: tooltips apenas suplementares; nomes acessíveis não dependem deles.
- Unsaved-changes behavior: exigir guard quando forms longos/editáveis forem introduzidos; previews clínicos atuais são read-only.
- Layer/z-index contract: topbar/nav < popover < dialog < toast futuro; não há drawer modal no hub atual.

## Async and resilience

- Mutation default: pessimista para autenticação, permissões, fila, diretório, financeiro e efeitos externos.
- Idempotency and duplicate-submit policy: botões de submit ficam bloqueados durante mutação; backend continua fonte de integridade.
- Auto-save/draft recovery: não existe nesta fase; não inventar para prontuário antes da change correspondente.
- Offline/read-stale/write behavior: falhas reais exibem erro persistente; não afirmar sucesso offline.
- Retry/backoff/timeout behavior: adicionar por capability quando houver integração remota; não retry automático de mutação não idempotente.
- Version conflict and multi-tab behavior: ainda não há contrato de edição concorrente além das constraints/services existentes.
- Session expiry/re-authentication: sessão inválida limpa contexto sensível e retorna ao login; 403 representa role insuficiente, não expiração.
- Long-running progress and return path: não aplicável nesta fase.
- Stale-request cancellation/invalidation and pending-state ownership: states que carregam dados devem impedir resposta antiga de substituir contexto novo quando busca remota for introduzida.
- Dialog/form preservation and retry after mutation failure: preservar valores não sensíveis; segredo de senha não é persistido.

## Validation

- Schema/validation layer: validação server-side em services/states das capabilities; HTML metadata ajuda entrada, mas não é fonte de autorização/integridade.
- Trigger timing: submit; campos já inválidos podem evoluir para feedback em blur/change quando a capability adotar field errors.
- Error summary/inline policy: erros curtos permanecem junto ao formulário/painel; forms clínicos longos futuros exigem summary + primeiro erro.
- Server error mapping: mensagens de negócio seguras; nunca stack trace/constraint/raw token.
- Sensitive-value handling: senha mascarada por padrão, `current-password`, sem log/toast/rota/persistência cliente.
- `noValidate`, first-invalid focus, duplicate-submit prevention, unsaved changes, and submit recovery: `noValidate` obrigatório em forms de produto; duplicate submit bloqueado; first-error/unsaved guard entram quando houver forms longos com field errors.

## Permission and clipboard

- Permission UI strategy: recursos irrelevantes à role ficam ausentes; rota direta incompatível vai para 403. O Admin pode ver previews visuais dos módulos dentro de `/admin`, mas isso não executa loaders/handlers protegidos de Recepção/Médico/Financeiro.
- Clipboard copy policy: quando segredo/identificador sensível for copiável, mostrar preview truncado e jamais incluir o valor no toast/log.
- Disabled-state explanation: controles demonstrativos sem backend devem estar disabled ou ser substituídos por ações de navegação de preview; não oferecer affordance de gravação falsa.

## Verification

- Required static commands: `python -m pytest -q`, `reflex compile --dry`, `npx -y @fission-ai/openspec@1.13.0 validate --specs`, lint oficial do `DESIGN.md` e auditor premium quando disponível no workspace completo.
- Browser/device/locale/theme matrix: desktop pequeno, desktop amplo, viewport estreito; `pt-BR`; light; reduced motion; forced colors quando disponível.
- Accessibility checks: teclado-only, foco visível, nomes acessíveis em icon buttons, labels reais, 403 próprio, contraste e reflow.
- Native-language/domain review and target-user evidence: copy clínica nova precisa revisão quando sair de preview e virar comportamento persistente.
- Component-state/visual regression coverage: login default/error/loading/reveal; admin preview desktop/mobile; empty/error/loading em módulos funcionais.
- Canonical sibling flow used for comparison: shells existentes de Recepção/Médico + `admin_directory_workspace()`.
- Project audit command/result: executar `audit_project.py <repo> --mode strict` no workspace completo antes de merge.
- CRUD full-flow evidence: testes atuais do diretório e fila + novos testes por capability quando persistência for adicionada.
- Failure-path evidence: auth/RBAC e testes de autorização existentes permanecem obrigatórios.