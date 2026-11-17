# QA de paridade das telas operacionais — 17/11/2026

## Escopo

Implementação verificada nas 16 rotas previstas pela change `align-operational-screen-visual-parity`:

| Referência | Rota |
|---|---|
| 01 — Dashboard da recepção | `/recepcao` |
| 02 — Agenda da recepção | `/recepcao/agenda` |
| 03 — Lista de pacientes | `/recepcao/pacientes` |
| 04 — Novo paciente | `/recepcao/pacientes/novo` |
| 05 — Fila de espera | `/recepcao/fila` |
| 06 — Dashboard da administração | `/admin` |
| 07 — Funcionários | `/admin/funcionarios` |
| 08 — Novo funcionário | `/admin/funcionarios/novo` |
| 09 — Especialidades | `/admin/especialidades` |
| 10 — Gerenciar horários | `/admin/horarios` |
| 11 — Configurações da clínica | `/admin/configuracoes` |
| 12 — Financeiro | `/financeiro` |
| 13 — Visão geral médica | `/medico` |
| 14 — Agenda médica | `/medico/agenda` |
| 15 — Pacientes vinculados | `/medico/pacientes` |
| 16 — Prontuário em atendimento | `/medico/prontuarios` |

O trabalho acrescenta projeções e composição visual aos módulos Reflex existentes. Serviços, autorização por papel e transições clínicas existentes foram mantidos; a agenda da recepção agora projeta a semana/dia selecionados a partir das consultas persistidas e informa consultas fora da faixa horária visível.

## Comparação visual

- Foram confirmadas 16 referências PNG locais e comparadas individualmente com Chromium em `1768×890`.
- O harness capturou as 16 rotas em seis viewports: `1768×890`, `1440×900`, `1024×768`, `768×1024`, `390×844` e `320×740`: **96/96 PASS**, sem falhas de rota ou overflow horizontal.
- O manifesto sanitizado de rota/viewports está em [operational-screen-parity-manifest-2026-11-17.json](operational-screen-parity-manifest-2026-11-17.json). Folhas de comparação e capturas individuais ficaram em `qa-artifacts/operational-reference/` (ignorado pelo Git). As quatro folhas `comparisons/comparativo-01-04.png` a `comparativo-13-16.png` foram inspecionadas visualmente após a captura final. As referências originais permaneceram fora do Git.
- A composição mantém navegação compacta em Recepção/Admin/Financeiro e expandida no Médico, usa os tokens canônicos (incluindo teal `#0F766E`) e ilustrações SVG autorais decorativas com leitores de tela ignorando a arte.
- Diferenças restantes são dependentes de dados e intencionais: a captura financeira sem cobranças elegíveis exibe `R$ 0,00`; a configuração sem dados salvos permanece vazia; painéis médicos exibem os registros sintéticos realmente vinculados em vez de forçar vazios. As ilustrações são recriações vetoriais próprias, não ativos originais localizados no projeto.

## Fluxos e integração

- Dashboards e listas derivam métricas de consultas, fila, pacientes, funcionários e mensagens persistidas, respeitando as leituras autorizadas no servidor. O painel de e-mail distingue solicitação aceita pelo Resend de entrega confirmada por webhook.
- As quatro telas médicas continuam limitadas aos vínculos e atendimentos autorizados; a chamada/prontuário atual usa o fluxo clínico existente. A agenda semanal respeita `America/Sao_Paulo`, não cria slots fictícios e conserva consulta fora do expediente na lista paginada.
- Logout e expiração também apagam as projeções operacionais de recepção, administração, agenda, configuração, funcionários e diretório médico, além dos estados clínicos já cobertos.
- As integrações Asaas e Resend e suas migrations já existiam na branch base. Esta change ajusta apresentação/indicadores e não duplica clientes, tabelas ou endpoints de provedor. Nenhuma migration nova foi criada; migrations existentes foram aplicadas somente nos bancos QA locais até `f031a5aa5002`.
- Não havia credenciais Asaas/Resend nem URL HTTPS pública de webhook disponíveis. Assim, não foram feitos envios ou chamadas externas e **não se declara homologação ponta a ponta**. Os clientes e webhooks permanecem testáveis por mocks; os requisitos de configuração estão em [asaas-resend-operacao.md](../asaas-resend-operacao.md) e `.env.example` não contém valores reais.

## Verificações

| Verificação | Resultado |
|---|---|
| PostgreSQL QA isolado: Alembic `upgrade head` | PASS — cadeia existente até `f031a5aa5002`; nenhuma migration nova nesta change |
| `pytest -q` | **560 passed, 3 skipped**, 1 aviso `StarletteDeprecationWarning` sobre `httpx` no `TestClient` |
| `pytest qa_browser/prescription_browser.py qa_browser/admin_agenda_browser.py -q` | **41 passed** após a correção de limpeza de sessão; inclui os fluxos de sessão, autorização, cadastro, reserva, atendimento, financeiro e responsividade |
| `python -m qa_browser.capture_operational_reference_screens` | **96/96 PASS**, comparação local das 16 telas e seis viewports |
| `reflex compile --dry` | PASS — compilado em 7,318 s; aparecem avisos de depreciação Reflex e duas anotações de handler já aceitas pelo compilador |
| OpenSpec `validate --all --strict --no-interactive` | **33 passed, 0 failed** |
| Engineering Plus quality gate `--full` | PASS em diff, heurística de segredos e pytest; `ruff` SKIP por não existir configuração |
| Engineering v3 quality gate `--full --security` | PASS em diff, heurística de segredos e testes; lint, typecheck, Gitleaks e Semgrep SKIP por não haver ferramentas/configuração |

As tentativas anteriores contra uma base QA vazia e contra a base QA reutilizada encontraram, respectivamente, ausência inicial de schema e colisão com um CPF sintético já persistido. Não foram alterações de produção. A suíte final foi repetida após `alembic upgrade head` em `vitta_one_operational_ui_qa_6` recém-criada e passou integralmente; a checagem isolada de concorrência que exige o nome `vitta_one` está entre os três skips dessa execução.

As execuções de navegador usaram somente contas `example.invalid` e registros sintéticos em bancos PostgreSQL QA recém-criados. A primeira tentativa reutilizou uma base QA preexistente: redefiniu a senha dos sete usuários `qa-*@example.invalid` e executou fluxos que acrescentaram ou alteraram somente dados QA sintéticos. A base não foi apagada nem teve o volume removido. Bancos adicionais de QA foram criados para obter uma base limpa e permitir repetição; nenhum foi removido.

## Limites restantes

- Homologação de cobrança e mensagens reais depende de chaves Sandbox/Resend, remetente verificado, destinatário autorizado e URL pública HTTPS para os webhooks. Nenhum desses requisitos foi simulado como concluído.
- Estado do GitHub verificado em 17/11/2026: a PR [#325 foi mesclada em `develop`](https://github.com/vitta-one/openspec/pull/325) em 01/11. A PR [#350 permanece aberta e marcada como `dirty`](https://github.com/vitta-one/openspec/pull/350); ela usa outro pacote financeiro (`vitta_one/finance`) e também altera arquivos compartilhados de UI/QA. Esta change foi baseada em `develop` `438b150`, reutiliza os módulos existentes `vitta_one/financial`/`vitta_one/notifications` e não incorpora a #350. A integração entre as branches precisa ser coordenada antes de qualquer merge.
- As capturas detalhadas e folhas comparativas locais não são versionadas para evitar incluir screenshots de referência e dados de navegador na PR. O workflow `qa-prescriptions-browser.yml` publica artefatos de Chromium sintéticos na execução associada à PR.
- Rollback desta change é reverter seus commits de feature. Não há migration nova a reverter; os bancos QA criados ficaram preservados.
