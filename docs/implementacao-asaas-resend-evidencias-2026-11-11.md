# Implementação Asaas/Resend — evidências de 11/11/2026

## Estado da entrega

Implementação adicionada na branch `feat/asaas-resend-openspec`, a partir de `develop` (`156b0a6`). Explore, Propose e Review concluídos antes do código. Apply realizado com verificação local; Verify completo e Archive continuam pendentes. A pedido do usuário, foram criadas somente variáveis de exemplo: ele fornecerá as credenciais no ambiente onde foi feito o deploy. Nenhum pagamento real, envio externo, merge ou deploy foi executado nesta sessão.

## OpenSpec

| Change | Artefatos | Validação | Arquivamento |
|---|---|---|---|
| integrate-asaas-financial | proposal, design, tasks, financial-management, asaas-payments, payment-notifications | strict válido; planejamento 4/4 | ativa, não arquivada |
| extend-resend-email | proposal, design, tasks, transactional-email, email-delivery, appointment-email-notifications | strict válido; planejamento 4/4 | ativa, não arquivada |

Validação global: `openspec validate --all --strict --no-interactive` retornou **32 itens aprovados e 0 falhas**. Há informação preexistente sobre delta `patient-portal` de outra change que impediria seu arquivamento porque o alvo consolidado ainda não existe. Essa change não foi alterada nem arquivada. Tasks só foram marcadas quando o resultado correspondente foi verificado; tasks com critérios de verificação adicionais permanecem abertas, inclusive quando já existe código parcial ou substancial.

## Implementação e arquivos

| Área | Arquivos principais | Resultado |
|---|---|---|
| Contratos e domínio financeiro | `vitta_one/financial/{asaas,service,application}.py` | Sandbox obrigatório, cliente/CPF, cobrança Pix/boleto, consulta/atualização, cancelamento e estorno integral Pix autorizado, resultado incerto sem repetição cega |
| Painel financeiro | `vitta_one/financial/{state,components}.py`, `ui/pages.py`, `ui/components.py`, `auth/state.py` | filtros, resumo SQL, evolução diária, paginação, detalhe/histórico, Pix copia e cola, confirmações; Financeiro e Administrador com guards próprios |
| Persistência | `models/financial.py`, `models/notification.py`, `models/__init__.py` | cliente/cobrança/histórico/inbox, preferências/auditoria, notificações/tentativas, eventos e solicitações de reenvio; sem duplicar prontuário |
| Transporte e templates | `notifications/{resend,templates}.py`, `professional_directory/email_sender.py` | adaptador central, HTML escapado e texto puro, layout fluido; senders públicos preservados |
| Comunicação e interface | `notifications/{service,state,operations}.py` | outbox, preferências por finalidade, supressão/revalidação, metadados de acesso, reenvio autorizado e auditável |
| Gatilhos existentes | `appointment_scheduling/service.py`, `patient_portal/service.py`, `professional_directory/state.py`, `ui/patient_directory_components.py` | intenção de agenda antes do commit; convites e credencial temporária preservados; escolhas independentes do consentimento de ativação |
| Endpoints | `integration_api.py`, `vitta_one.py` | POST `/api/webhooks/asaas` e `/api/webhooks/resend`, integrados à API Reflex existente; ativação do portal preservada |
| Processamento | `integration_worker.py` | lote limitado; modo `--watch` a cada cinco minutos; inbox/outbox duráveis, sem chamar Resend no recebimento Asaas |
| Configuração | `.env.example`, `requirements.txt`, `docs/asaas-resend-operacao.md` | nomes sem segredos; nova dependência Svix 2.10.0 para assinatura oficial |

Migrations aditivas: `f031a5aa5001_add_asaas_financial.py` e `f031a5aa5002_add_transactional_notifications.py`. Cabeça única `f031a5aa5002`, sobre `e9d3a8c2b170`. Não foram aplicadas a banco existente. `reflex.lock/package.json` já continha marcadores de conflito na base; foi preservado o conteúdo JSON completo de uma das versões existentes, removendo os marcadores para permitir inicialização/compilação. Nenhum framework novo foi introduzido.

## Evidências de qualidade

- Python isolado: 3.12.14, Reflex 0.9.10.post2; dependências instaladas em `.venv/`, não versionada.
- Execução ampliada de todos os arquivos de teste que não terminam em `_postgres.py`: **491 aprovados, 24 ignorados, 0 falhas**, em 47,57s. Os 24 skips incluem a parametrização PostgreSQL das novas integrações, concorrência que exige locks PostgreSQL e um skip já existente.
- Novos testes: `test_asaas_contract.py`, `test_financial_notifications.py`, `test_integration_migrations.py`; regressões de navegação ajustadas à promoção aprovada de `/admin/financeiro`.
- Os testes cobrem contratos HTTP simulados, rejeição de produção, valores inválidos, ausência de configuração, Pix/boleto, emissão duplicada, timeout/recuperação sem segundo POST, CPF externo já existente, atualização de cliente, permissão financeira, sessão inválida/expirada/provisória, cancelamento, estorno recusado, evento duplicado/fora de ordem e independência clínica.
- Comunicação: gatilhos transacionais de agenda, consentimento/revogação, deduplicação, UNKNOWN sem reenvio cego, intenção removida em rollback financeiro, lembrete atrasado suprimido, aceite distinto de entrega, escape HTML, metadados de acesso sem segredo e prevenção de segundo envio.
- Webhooks: token Asaas, assinatura Svix válida/forjada, replay antigo, duplicidade e limite de 256 KiB; nenhuma chamada real aos provedores.
- `reflex compile --dry`: aprovado (última execução registrada: 15,921s). Permanecem avisos preexistentes de depreciação, ícones e anotações de eventos em módulos anteriores.
- `python -m compileall -q vitta_one`: aprovado; `python -m vitta_one.integration_worker --help`: aprovado.
- Migrations: teste de upgrade/downgrade das duas revisions em SQLite isolado aprovado, comparando colunas com os modelos e preservando tabelas clínicas; geração SQL PostgreSQL offline e `alembic heads` aprovados. Isso não é execução PostgreSQL.
- `git diff --check`: aprovado.

## Simulação, Sandbox e produção

| Ambiente | Resultado |
|---|---|
| Contratos simulados e SQLite | verificados conforme testes acima |
| PostgreSQL real | migrações e suite automatizada aprovadas no CI; servidor local não disponível |
| Asaas Sandbox real | não executado; aguarda credenciais e configuração de webhook |
| Resend real | não executado; aguarda chave, remetente e destinatário de teste autorizado |
| Navegador desktop/mobile | compilação concluída; fluxo visual/E2E ainda não validado |
| Produção | nenhuma alteração ou operação executada |

Uma tentativa inicial de executar a suite completa foi interrompida ao chegar aos testes que exigem PostgreSQL, pois a URL usada para importação/compilação apontava apenas para um endereço local de teste sem servidor. O resultado válido acima exclui explicitamente esses arquivos. Não se converteu falha de conexão em sucesso nem se usou SQLite como prova de locks PostgreSQL.

## Pendências antes do aceite

1. Configurar variáveis no backend do ambiente de teste e aplicar migrations revisadas; configurar um worker supervisionado ou agendamento de cinco minutos.
2. Concluir cenários específicos de reinício/leases e downgrade PostgreSQL ainda abertos nas tasks. A suite integral e as migrations upgrade já passaram no CI PostgreSQL; os testes novos exigem `VITTA_ONE_QA_DISPOSABLE_DATABASE=yes` e usam schema temporário próprio.
3. Validar UI desktop/mobile, teclado, confirmações, preferências, pesquisa/paginação e fluxo login → paciente → reserva → cobrança → webhook → notificação/histórico em navegador.
4. Homologar APIs e webhooks reais no Asaas Sandbox e Resend, com dados sintéticos e destinatário autorizado; revisar limitações efetivas da conta para Pix/boleto/estorno.
5. Completar as verificações específicas ainda abertas em tasks, comparar implementação com specs, sincronizar e arquivar oficialmente apenas após aceite comprovado.

Cartão, recuperação pública de senha, aviso de vencimento e documento fiscal continuam fora do escopo homologado, conforme aprovação. Registros SENDING/UNKNOWN e vínculos externos ambíguos devem ser revisados, nunca liberados para novo POST por suposição. Esta entrega não satisfaz ainda os critérios de integração real e E2E exigidos para considerar as changes concluídas.

## Git e revisão

PR em rascunho: [#351](https://github.com/vitta-one/openspec/pull/351), base `develop`, branch `feat/asaas-resend-openspec`. Commits por etapa: `6b1cd5e` (auditoria e OpenSpec), `ecb1810` (backend e persistência), `6ce5a3d` (interface Reflex) e `c13fbea` (testes e operação), além da atualização final deste relatório. Nenhum merge/deploy efetuado.

## Evidência adicional no ambiente remoto

[Validate Vitta-One](https://github.com/vitta-one/openspec/actions/runs/43024998845) concluiu com sucesso no commit `de268a3`: migração no PostgreSQL descartável, suite integral Pytest, validação OpenSpec e compilação Reflex. A configuração desse workflow habilita os testes PostgreSQL e `VITTA_ONE_QA_DISPOSABLE_DATABASE=yes`. Assim, a limitação de PostgreSQL local foi suprida pelo CI para os cenários automatizados presentes. Isso não cobre automaticamente todos os cenários específicos ainda abertos nas tasks nem substitui homologação dos provedores ou E2E das novas telas.

O quadro anterior descreve a disponibilidade local no momento da execução; PostgreSQL foi posteriormente verificado no ambiente remoto. Downgrade das novas revisions em PostgreSQL e cenários adicionais de reinício/leases continuam com tarefas próprias abertas.

## Manifesto de arquivos da branch

| Situação | Arquivo |
|---|---|
| Criado | `.env.example` |
| Alterado | `.gitignore` |
| Criado | `alembic/versions/f031a5aa5001_add_asaas_financial.py` |
| Criado | `alembic/versions/f031a5aa5002_add_transactional_notifications.py` |
| Criado | `docs/asaas-resend-operacao.md` |
| Criado | `docs/auditoria-asaas-resend-2026-11-11.md` |
| Criado | `docs/implementacao-asaas-resend-evidencias-2026-11-11.md` |
| Criado | `docs/revisao-asaas-resend-2026-11-11.md` |
| Criado | `openspec/changes/extend-resend-email/.openspec.yaml` |
| Criado | `openspec/changes/extend-resend-email/design.md` |
| Criado | `openspec/changes/extend-resend-email/proposal.md` |
| Criado | `openspec/changes/extend-resend-email/specs/appointment-email-notifications/spec.md` |
| Criado | `openspec/changes/extend-resend-email/specs/email-delivery/spec.md` |
| Criado | `openspec/changes/extend-resend-email/specs/transactional-email/spec.md` |
| Criado | `openspec/changes/extend-resend-email/tasks.md` |
| Criado | `openspec/changes/integrate-asaas-financial/.openspec.yaml` |
| Criado | `openspec/changes/integrate-asaas-financial/design.md` |
| Criado | `openspec/changes/integrate-asaas-financial/proposal.md` |
| Criado | `openspec/changes/integrate-asaas-financial/specs/asaas-payments/spec.md` |
| Criado | `openspec/changes/integrate-asaas-financial/specs/financial-management/spec.md` |
| Criado | `openspec/changes/integrate-asaas-financial/specs/payment-notifications/spec.md` |
| Criado | `openspec/changes/integrate-asaas-financial/tasks.md` |
| Alterado | `reflex.lock/package.json` |
| Alterado | `requirements.txt` |
| Alterado | `tests/test_admin_task_routes.py` |
| Criado | `tests/test_asaas_contract.py` |
| Criado | `tests/test_financial_notifications.py` |
| Criado | `tests/test_integration_migrations.py` |
| Alterado | `tests/test_shell_navigation.py` |
| Alterado | `vitta_one/appointment_scheduling/service.py` |
| Alterado | `vitta_one/auth/state.py` |
| Criado | `vitta_one/financial/__init__.py` |
| Criado | `vitta_one/financial/application.py` |
| Criado | `vitta_one/financial/asaas.py` |
| Criado | `vitta_one/financial/components.py` |
| Criado | `vitta_one/financial/service.py` |
| Criado | `vitta_one/financial/state.py` |
| Criado | `vitta_one/integration_api.py` |
| Criado | `vitta_one/integration_worker.py` |
| Alterado | `vitta_one/models/__init__.py` |
| Criado | `vitta_one/models/financial.py` |
| Criado | `vitta_one/models/notification.py` |
| Criado | `vitta_one/notifications/__init__.py` |
| Criado | `vitta_one/notifications/operations.py` |
| Criado | `vitta_one/notifications/resend.py` |
| Criado | `vitta_one/notifications/service.py` |
| Criado | `vitta_one/notifications/state.py` |
| Criado | `vitta_one/notifications/templates.py` |
| Alterado | `vitta_one/patient_portal/service.py` |
| Alterado | `vitta_one/professional_directory/email_sender.py` |
| Alterado | `vitta_one/professional_directory/state.py` |
| Alterado | `vitta_one/ui/components.py` |
| Alterado | `vitta_one/ui/pages.py` |
| Alterado | `vitta_one/ui/patient_directory_components.py` |
| Alterado | `vitta_one/vitta_one.py` |

## Resultado final das verificações remotas

- [Validate Vitta-One](https://github.com/vitta-one/openspec/actions/runs/43024998845): **529 testes aprovados, 1 ignorado**, migrations PostgreSQL e compilação aprovadas no commit de268a3.
- [Chromium](https://github.com/vitta-one/openspec/actions/runs/43024998828): **16 aprovados e 19 com falha**, em 565,70s. A etapa de agenda administrativa e a captura completa não executaram após a falha. Não há aceite E2E completo.
- Artefatos da execução: [evidências sintéticas](https://github.com/vitta-one/openspec/actions/runs/43024998828/artifacts/13857596478).

### Diagnóstico das falhas Chromium

Os logs apontam expectativas incompatíveis com a UI existente. A comparação estática com develop confirmou:

| Expectativa do teste | Código atual já existente na base | Evidência de escopo |
|---|---|---|
| Heading Recepção — Operação do Dia | `reception/dashboard/components.py:399` exibe Recepção | arquivo sem diff nesta branch |
| Botão Abrir ou fechar navegação | `ui/components.py:622,631` usa Recolher/Expandir e Abrir/Fechar navegação | diff desse arquivo altera somente o item financeiro no menu |
| Criar funcionário abre /admin/funcionarios | `ui/admin_hub_components.py:58` direciona a /admin/funcionarios/novo | arquivo sem diff nesta branch |
| Especialidades como role=listitem | diretório utiliza tabela, não a antiga lista | `ui/admin_directory_components.py` sem diff nesta branch |
| Link Especialidades único em toda a página | há link de navegação e link de conteúdo | seletor sem escopo causou strict mode violation |

Isso fundamenta a necessidade de atualizar a suite em relação às changes de UI anteriores, mas não é uma execução comparativa de navegador da develop. Portanto, não se declara automaticamente que todas as 19 falhas são preexistentes ou irrelevantes. Os testes não foram removidos, enfraquecidos ou marcados como sucesso. A interface deve passar por revisão E2E específica antes do aceite.

O único skip da suite integral é registrado no log do CI; a contagem local 491/24 descreve outra seleção de ambiente e não deve ser somada à contagem remota. O PR permanece em rascunho e as duas changes permanecem ativas.
