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
| PostgreSQL real | não disponível localmente; testes preparados, execução pendente |
| Asaas Sandbox real | não executado; aguarda credenciais e configuração de webhook |
| Resend real | não executado; aguarda chave, remetente e destinatário de teste autorizado |
| Navegador desktop/mobile | compilação concluída; fluxo visual/E2E ainda não validado |
| Produção | nenhuma alteração ou operação executada |

Uma tentativa inicial de executar a suite completa foi interrompida ao chegar aos testes que exigem PostgreSQL, pois a URL usada para importação/compilação apontava apenas para um endereço local de teste sem servidor. O resultado válido acima exclui explicitamente esses arquivos. Não se converteu falha de conexão em sucesso nem se usou SQLite como prova de locks PostgreSQL.

## Pendências antes do aceite

1. Configurar variáveis no backend do ambiente de teste e aplicar migrations revisadas; configurar um worker supervisionado ou agendamento de cinco minutos.
2. Executar suite integral, concorrência/leases/outbox e migrations em PostgreSQL descartável. A nova suite exige também `VITTA_ONE_QA_DISPOSABLE_DATABASE=yes` e usa schema temporário próprio.
3. Validar UI desktop/mobile, teclado, confirmações, preferências, pesquisa/paginação e fluxo login → paciente → reserva → cobrança → webhook → notificação/histórico em navegador.
4. Homologar APIs e webhooks reais no Asaas Sandbox e Resend, com dados sintéticos e destinatário autorizado; revisar limitações efetivas da conta para Pix/boleto/estorno.
5. Completar as verificações específicas ainda abertas em tasks, comparar implementação com specs, sincronizar e arquivar oficialmente apenas após aceite comprovado.

Cartão, recuperação pública de senha, aviso de vencimento e documento fiscal continuam fora do escopo homologado, conforme aprovação. Registros SENDING/UNKNOWN e vínculos externos ambíguos devem ser revisados, nunca liberados para novo POST por suposição. Esta entrega não satisfaz ainda os critérios de integração real e E2E exigidos para considerar as changes concluídas.

## Git e revisão

PR em rascunho: [#351](https://github.com/vitta-one/openspec/pull/351), base `develop`, branch `feat/asaas-resend-openspec`. Commits por etapa: `6b1cd5e` (auditoria e OpenSpec), `ecb1810` (backend e persistência), `6ce5a3d` (interface Reflex) e `c13fbea` (testes e operação), além da atualização final deste relatório. Nenhum merge/deploy efetuado.
