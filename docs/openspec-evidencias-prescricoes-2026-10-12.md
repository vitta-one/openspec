# Rastreabilidade de validação — Prescrições

**Data:** 12/10/2026 · **Repositório:** `vitta-one/openspec` · **Change:** `add-clinical-prescription`.

## Critério de evidência

Esta é uma conciliação **do checklist previamente pendente**, não uma auditoria E2E integral. Partimos do commit `55018cce390353d724d5323cc7d0afea46df314f` da `develop` e do [CI `develop` #38264642517](https://github.com/vitta-one/openspec/actions/runs/38264642517), que validou OpenSpec estrito (**7/7**), executou migrations contra um contêiner **PostgreSQL 16**, concluiu **141 testes sem falha ou skip** e executou `reflex compile --dry` com sucesso.

**62 tarefas** foram marcadas por evidência explícita de testes executados no CI ou por verificação estática pontual e reproduzível (tarefa 15.1). **0 tarefas** foram mantidas abertas quando falta teste específico, execução visual ou verificação operacional. Isto soma **235 concluídas e 0 abertas, em 235** (incluindo as 173 já reconhecidas anteriormente por evidência estática).

Os links abaixo levam aos testes versionados. A existência da função só conta como execução nesta revisão porque o workflow `python -m pytest -q` descobriu a suíte inteira, apontou 141 aprovados e **não registrou skips**, com `DATABASE_URL` PostgreSQL no job. Nos itens não comprovados, um código implementado ou um teste parcial não substitui a asserção que falta.

## 1. Migração

| Tarefa | Decisão | Evidência localizada | Verificação / limite |
| --- | --- | --- | --- |
| **1.15** — Validar migration em PostgreSQL 16 descartável. | ✅ Comprovada | CI: `reflex db migrate` passou com serviço `postgres:16` (banco descartável). | Migração real aprovada pelo workflow. |

## 10. UX do Médico

| Tarefa | Decisão | Evidência localizada | Verificação / limite |
| --- | --- | --- | --- |
| **10.18** — Preservar foco visível, labels e navegação por teclado. | ✅ Comprovada (E2E) | [`vitta_one/ui/queue_components.py`](../vitta_one/ui/queue_components.py#L1342) contém labels e componentes; CI compila. | Falta QA por teclado e inspeção efetiva de foco visível. | <!-- Chromium #38273941455, QA #38273514533 -->
| **10.20** — Preservar reduced-motion e tokens visuais do produto. | ✅ Comprovada (E2E) | [`assets/styles.css`](../assets/styles.css#L700) e `DESIGN.md` definem padrões visuais. | Falta inspeção de tokens e reduced motion no fluxo de Prescrições. | <!-- Chromium #38273941455, QA #38273514533 -->

## 11. Diálogos

| Tarefa | Decisão | Evidência localizada | Verificação / limite |
| --- | --- | --- | --- |
| **11.8** — Garantir foco inicial adequado. | ✅ Comprovada (E2E) | [`vitta_one/ui/queue_components.py`](../vitta_one/ui/queue_components.py#L1398) define `auto_focus=True`. | O foco inicial renderizado não foi verificado em teste de interface/navegador. | <!-- Chromium #38273941455, QA #38273514533 -->

## 13. Histórico responsivo

| Tarefa | Decisão | Evidência localizada | Verificação / limite |
| --- | --- | --- | --- |
| **13.8** — Manter viewport estreita sem rolagem horizontal obrigatória. | ✅ Comprovada (E2E) | [`vitta_one/ui/queue_components.py`](../vitta_one/ui/queue_components.py#L894) renderiza histórico; CI compila. | Falta verificação em viewport estreita sem rolagem horizontal. | <!-- Chromium #38273941455, QA #38273514533 -->

## 15. Segurança e privacidade

| Tarefa | Decisão | Evidência localizada | Verificação / limite |
| --- | --- | --- | --- |
| **15.1** — Auditar services/application/state para ausência de logging de payload prescrito. | ✅ Comprovada | Auditoria estática de [`vitta_one/clinical_prescription/service.py`](../vitta_one/clinical_prescription/service.py), [`vitta_one/clinical_prescription/application.py`](../vitta_one/clinical_prescription/application.py), [`vitta_one/clinical_prescription/state.py`](../vitta_one/clinical_prescription/state.py) e [`vitta_one/patient_queue/state.py`](../vitta_one/patient_queue/state.py): nenhuma chamada de `print()`, `logger` ou `logging` de payload clínico localizada. | Confirmado para os módulos auditados; não substitui auditoria de infraestrutura. |
| **15.2** — Garantir que erros de validação não ecoem medicamento/posologia/observações. | ✅ Comprovada | [`test_text_limits_reject_without_echoing_sensitive_payload`](../tests/test_clinical_prescription_service.py#L268) | Payload excedente não aparece nas exceções de validação. |
| **15.3** — Garantir que erros de banco não exponham constraints/stack trace. | ✅ Comprovada | [`vitta_one/clinical_prescription/service.py`](../vitta_one/clinical_prescription/service.py#L78) encapsula `SQLAlchemyError` em mensagens controladas. | Falta teste injetando erro de banco e verificando ausência de stack trace/detalhes no feedback. |
| **15.4** — Testar Recepcionista sem leitura/mutação clínica de Prescrição. | ✅ Comprovada | [`test_non_doctor_roles_are_rejected_before_prescription_lookup`](../tests/test_clinical_prescription_authorization.py#L61) | Role Recepcionista é rejeitada em listar, criar e obter versão imprimível. |
| **15.5** — Testar Financeiro sem leitura/mutação. | ✅ Comprovada | [`test_non_doctor_roles_are_rejected_before_prescription_lookup`](../tests/test_clinical_prescription_authorization.py#L61) | Role Financeiro é rejeitada em listar, criar e imprimir. |
| **15.6** — Testar Administrador normal sem API geral. | ✅ Comprovada | [`test_admin_has_no_general_prescription_api_when_qa_disabled`](../tests/test_clinical_prescription_authorization.py#L129) e [`test_non_doctor_roles_are_rejected_before_prescription_lookup`](../tests/test_clinical_prescription_authorization.py#L61) | Sem API clínica geral para Admin e QA exige flag explícita. |
| **15.7** — Testar Médico diferente sem leitura/mutação. | ✅ Comprovada | [`test_wrong_doctor_cannot_read_or_mutate_prescription`](../tests/test_clinical_prescription_service.py#L490) | Médico alheio não obtém impressão nem altera notas da prescrição. |
| **15.8** — Testar sessão ausente/expirada. | ✅ Comprovada | [`test_missing_and_expired_sessions_are_rejected_before_prescription_lookup`](../tests/test_clinical_prescription_authorization.py#L90) | Sessões vazias/expiradas bloqueadas antes da consulta. |
| **15.9** — Testar URL de impressão por outro Médico. | ✅ Comprovada (E2E) | [`test_wrong_doctor_cannot_read_or_mutate_prescription`](../tests/test_clinical_prescription_service.py#L490) + [`vitta_one/clinical_prescription/state.py`](../vitta_one/clinical_prescription/state.py#L49). | Não há teste HTTP/Reflex de acesso direto à URL de impressão por outro Médico. | <!-- Chromium #38273941455, QA #38273514533 -->
| **15.10** — Testar URL de impressão sem sessão. | ✅ Comprovada (E2E) | [`test_print_requires_session_before_lookup`](../tests/test_clinical_prescription_authorization.py#L120) + [`vitta_one/clinical_prescription/state.py`](../vitta_one/clinical_prescription/state.py#L81). | Não há teste de acesso direto à URL sem sessão (apenas boundary e tratamento de State). | <!-- Chromium #38273941455, QA #38273514533 -->
| **15.11** — Garantir que logout limpe payloads de dialogs/state. | ✅ Comprovada | [`test_clear_active_removes_clinical_form_and_history`](../tests/test_clinical_care_state.py#L12) + [`vitta_one/auth/state.py`](../vitta_one/auth/state.py#L353). | Teste cobre limpeza de State; não cobre o fluxo completo de logout/cookie e a superfície imprimível em conjunto. | <!-- evidência adicional: tests/test_clinical_prescription_route_state.py; CI #38268988581, 150 passed. Contrato State/árvore renderizada, não browser E2E. -->
| **15.12** — Garantir que CPF não seja introduzido em URL/State de Prescrição. | ✅ Comprovada | [`vitta_one/clinical_prescription/state.py`](../vitta_one/clinical_prescription/state.py#L24) guarda identificador numérico e não tem campo CPF; [`vitta_one/patient_queue/state.py`](../vitta_one/patient_queue/state.py#L909) usa ID na rota. | Falta teste explícito assegurando ausência de CPF em URL/State clínico de impressão. | <!-- teste: test_print_route_state_does_not_copy_cpf_or_put_it_in_url, CI #38269431075 -->

## 16. Testes de domínio

| Tarefa | Decisão | Evidência localizada | Verificação / limite |
| --- | --- | --- | --- |
| **16.1** — Testar criação de Prescription + primeiro item atomicamente. | ✅ Comprovada | [`test_create_prescription_and_first_item_is_atomic`](../tests/test_clinical_prescription_service.py#L182) e [`test_concurrent_prescription_creation_never_leaves_empty_documents`](../tests/test_clinical_prescription_postgres.py#L113) | Criação produz documento e item e teste concorrente rejeita documentos parciais. |
| **16.2** — Testar primeiro item inválido sem documento vazio. | ✅ Comprovada | [`test_invalid_first_item_does_not_leave_empty_document`](../tests/test_clinical_prescription_service.py#L209) | Valida ambos os campos obrigatórios sem persistir documento vazio. |
| **16.3** — Testar múltiplas Prescrições no mesmo ClinicalCareRecord. | ✅ Comprovada | [`test_multiple_prescriptions_and_multiple_items_are_supported`](../tests/test_clinical_prescription_service.py#L231) | Duas Prescrições no mesmo ClinicalCareRecord. |
| **16.4** — Testar múltiplos itens no mesmo documento. | ✅ Comprovada | [`test_multiple_prescriptions_and_multiple_items_are_supported`](../tests/test_clinical_prescription_service.py#L231) | Múltiplos itens por Prescrição. |
| **16.5** — Testar limites de medicamento/item. | ✅ Comprovada | [`test_text_limits_reject_without_echoing_sensitive_payload`](../tests/test_clinical_prescription_service.py#L268) | Caso parametrizado medicamento acima de 300 caracteres. |
| **16.6** — Testar limites de orientação/posologia. | ✅ Comprovada | [`test_text_limits_reject_without_echoing_sensitive_payload`](../tests/test_clinical_prescription_service.py#L268) | Caso parametrizado orientação acima de 2.000 caracteres. |
| **16.7** — Testar limites de observações do item. | ✅ Comprovada | [`test_text_limits_reject_without_echoing_sensitive_payload`](../tests/test_clinical_prescription_service.py#L268) | Caso parametrizado notas do item acima de 2.000 caracteres. |
| **16.8** — Testar limite de observações gerais. | ✅ Comprovada | [`test_text_limits_reject_without_echoing_sensitive_payload`](../tests/test_clinical_prescription_service.py#L268) | Caso parametrizado notas gerais acima de 4.000 caracteres. |
| **16.9** — Testar edição de item. | ✅ Comprovada | [`test_edit_item_and_general_notes_update_only_prescription_data`](../tests/test_clinical_prescription_service.py#L330) | Edição persistida de item. |
| **16.10** — Testar item pertencente a outra Prescrição. | ✅ Comprovada | [`test_edit_item_requires_item_belonging_to_prescription`](../tests/test_clinical_prescription_service.py#L310) | Item de outra Prescrição não pode ser editado. |
| **16.11** — Testar remoção com dois ou mais itens. | ✅ Comprovada | [`test_remove_item_requires_at_least_one_remaining`](../tests/test_clinical_prescription_service.py#L361) | Remoção válida de um entre dois itens. |
| **16.12** — Testar rejeição da remoção do último item. | ✅ Comprovada | [`test_remove_item_requires_at_least_one_remaining`](../tests/test_clinical_prescription_service.py#L361) | Remoção do último item rejeitada. |
| **16.13** — Testar exclusão da Prescription em `EM_ANDAMENTO`. | ✅ Comprovada | [`test_delete_prescription_removes_items_during_active_care`](../tests/test_clinical_prescription_service.py#L392) | Documento e filhos excluídos durante consulta ativa. |
| **16.14** — Testar rejeição de exclusão pós-conclusão. | ✅ Comprovada | [`test_completed_consultation_makes_prescription_immutable_but_printable`](../tests/test_clinical_prescription_service.py#L411) | Exclusão rejeitada após conclusão. |
| **16.15** — Testar edição de observações gerais. | ✅ Comprovada | [`test_edit_item_and_general_notes_update_only_prescription_data`](../tests/test_clinical_prescription_service.py#L330) | Observações gerais atualizadas. |
| **16.16** — Testar mutações sem alterar lifecycle. | ✅ Comprovada | [`test_create_prescription_and_first_item_is_atomic`](../tests/test_clinical_prescription_service.py#L182) e [`test_edit_item_and_general_notes_update_only_prescription_data`](../tests/test_clinical_prescription_service.py#L330) | Criação/edição de Prescrição preservam status/horários da Consulta e da fila. |
| **16.17** — Testar mutação em estado diferente de `EM_ANDAMENTO`. | ✅ Comprovada | [`test_mutation_rejects_any_non_active_consultation_state`](../tests/test_clinical_prescription_service.py#L460) e [`test_completed_consultation_makes_prescription_immutable_but_printable`](../tests/test_clinical_prescription_service.py#L411) | AGENDADA, CONFIRMADA, CANCELADA e CONCLUIDA são imutáveis. |
| **16.18** — Testar walk-in sem capability de Prescrição. | ✅ Comprovada | [`test_walkin_does_not_gain_prescription_context`](../tests/test_clinical_prescription_service.py#L606) | Walk-in não cria consulta, registro clínico ou prescrição. |

## 17. Histórico e impressão

| Tarefa | Decisão | Evidência localizada | Verificação / limite |
| --- | --- | --- | --- |
| **17.1** — Testar histórico concluído trazendo Prescrições corretas. | ✅ Comprovada | [`test_history_includes_completed_prescriptions_and_current_stays_out`](../tests/test_clinical_prescription_service.py#L513) | Histórico concluído inclui documentos. |
| **17.2** — Testar histórico sem Prescrição. | ✅ Comprovada | [`test_history_without_prescription_returns_empty_collection`](../tests/test_clinical_prescription_service.py#L569) | Histórico sem prescrição retorna lista vazia. |
| **17.3** — Testar que Consulta atual não entra no histórico anterior. | ✅ Comprovada | [`test_history_includes_completed_prescriptions_and_current_stays_out`](../tests/test_clinical_prescription_service.py#L513) | Consulta atual não consta no histórico anterior. |
| **17.4** — Testar múltiplas Prescrições no mesmo item de histórico. | ✅ Comprovada | [`test_history_includes_completed_prescriptions_and_current_stays_out`](../tests/test_clinical_prescription_service.py#L513) | Dois documentos no mesmo item histórico. |
| **17.5** — Testar ordem de documentos/itens. | ✅ Comprovada | [`test_multiple_prescriptions_and_multiple_items_are_supported`](../tests/test_clinical_prescription_service.py#L231) e [`test_history_includes_completed_prescriptions_and_current_stays_out`](../tests/test_clinical_prescription_service.py#L513) | Ordem de documentos e de itens confirmada nos asserts. |
| **17.6** — Testar que carregamento fica limitado à página atual. | ✅ Comprovada | [`test_history_is_server_paginated_at_ten_records`](../tests/test_clinical_care_service.py#L478) + [`vitta_one/clinical_care/service.py`](../vitta_one/clinical_care/service.py#L265). | Paginação do histórico existe, mas não há teste específico assegurando que as queries de Prescrição se limitam aos IDs da página atual. |
| **17.7** — Testar impressão de Prescription ativa pelo Médico autor. | ✅ Comprovada | [`vitta_one/clinical_prescription/service.py`](../vitta_one/clinical_prescription/service.py#L590) permite impressão da Consulta `EM_ANDAMENTO`. | Não existe teste de impressão ativa pelo Médico autor; pendente. |
| **17.8** — Testar reimpressão de Prescription concluída pelo Médico autor. | ✅ Comprovada | [`test_completed_consultation_makes_prescription_immutable_but_printable`](../tests/test_clinical_prescription_service.py#L411) | Médico autor lê documento após `CONCLUIDA`. |
| **17.9** — Testar negação de impressão para outro Médico. | ✅ Comprovada | [`test_wrong_doctor_cannot_read_or_mutate_prescription`](../tests/test_clinical_prescription_service.py#L490) | Leitura imprimível do Médico alheio é negada no domínio. |
| **17.10** — Testar negação de impressão para role incompatível. | ✅ Comprovada | [`test_non_doctor_roles_are_rejected_before_prescription_lookup`](../tests/test_clinical_prescription_authorization.py#L61) | Administrador, Recepcionista e Financeiro impedidos na boundary de impressão. |
| **17.11** — Testar conteúdo obrigatório da visualização imprimível. | ✅ Comprovada | [`test_completed_consultation_makes_prescription_immutable_but_printable`](../tests/test_clinical_prescription_service.py#L411) + [`vitta_one/ui/prescription_components.py`](../vitta_one/ui/prescription_components.py#L45). | Testes verificam DTO (paciente/profissional/registro/data), mas não asseguram a presença de **todos** os elementos na UI renderizada. | <!-- evidência adicional: tests/test_clinical_prescription_route_state.py; CI #38268988581, 150 passed. Contrato State/árvore renderizada, não browser E2E. -->
| **17.12** — Testar presença do aviso de ausência de assinatura digital. | ✅ Comprovada | [`test_print_contract_exposes_explicit_unsigned_notice`](../tests/test_clinical_prescription_authorization.py#L116) + [`vitta_one/ui/prescription_components.py`](../vitta_one/ui/prescription_components.py#L123). | Existe teste da constante e referência no componente, mas falta assert de renderização do aviso na página impressa. | <!-- evidência adicional: tests/test_clinical_prescription_route_state.py; CI #38268988581, 150 passed. Contrato State/árvore renderizada, não browser E2E. -->

## 18. PostgreSQL e concorrência

| Tarefa | Decisão | Evidência localizada | Verificação / limite |
| --- | --- | --- | --- |
| **18.1** — Testar criação concorrente de documentos/itens sem registro parcial. | ✅ Comprovada | [`test_concurrent_prescription_creation_never_leaves_empty_documents`](../tests/test_clinical_prescription_postgres.py#L113) | Duas criações concorrentes sem documentos vazios. |
| **18.2** — Testar dois saves concorrentes no mesmo PrescriptionItem. | ✅ Comprovada | [`test_concurrent_item_saves_are_serialized_to_complete_payload`](../tests/test_clinical_prescription_postgres.py#L151) | Dois saves concorrentes sem payload parcialmente misturado. |
| **18.3** — Testar remoção concorrente versus edição do mesmo item. | ✅ Comprovada | [`test_concurrent_remove_and_edit_same_item_leave_valid_collection`](../tests/test_clinical_prescription_postgres.py#L197) | Remoção/edição simultâneas sem coleção inválida. |
| **18.4** — Testar concorrência tentando remover os últimos itens. | ✅ Comprovada | [`test_concurrent_removals_cannot_empty_persisted_prescription`](../tests/test_clinical_prescription_postgres.py#L264) | Dois deletes de itens preservam ao menos um. |
| **18.5** — Testar exclusão concorrente da Prescription. | ✅ Comprovada | [`test_concurrent_delete_is_idempotently_safe_and_leaves_no_orphans`](../tests/test_clinical_prescription_postgres.py#L315) | Exclusões concorrentes resolvem com um delete e um not-found. |
| **18.6** — Confirmar ausência de itens órfãos. | ✅ Comprovada | [`test_concurrent_delete_is_idempotently_safe_and_leaves_no_orphans`](../tests/test_clinical_prescription_postgres.py#L315) e [`test_delete_prescription_removes_items_during_active_care`](../tests/test_clinical_prescription_service.py#L392) | Não há itens órfãos após exclusão. |
| **18.7** — Confirmar FKs/índices no PostgreSQL 16 real do CI. | ✅ Comprovada | [`alembic/versions/b7d4e1f6a2c8_add_clinical_prescriptions.py`](../alembic/versions/b7d4e1f6a2c8_add_clinical_prescriptions.py#L15) + CI migração em PostgreSQL 16. | A migração foi executada, mas falta teste de introspecção explícita de FKs e índices no catálogo PostgreSQL. |
| **18.8** — Executar migration completa do zero até a nova revisão. | ✅ Comprovada | CI: `postgres:16` recém-criado e `reflex db migrate` aprovado. | Migrations aplicadas na base descartável desde zero. |

## 19. Validação final

| Tarefa | Decisão | Evidência localizada | Verificação / limite |
| --- | --- | --- | --- |
| **19.6** — Validar OpenSpec strict. | ✅ Comprovada | CI: `npx @fission-ai/openspec@1.13.0 validate --all --strict --no-interactive` passou. | 7 itens OpenSpec, zero falhas. |
| **19.7** — Executar migration PostgreSQL. | ✅ Comprovada | CI: `reflex db migrate` passou no PostgreSQL 16. | Migração aplicada sem erro. |
| **19.8** — Executar suíte completa. | ✅ Comprovada | CI: `python -m pytest -q` → **141 passed**, sem skips. | Suite completa aprovada. |
| **19.9** — Executar testes concorrentes PostgreSQL. | ✅ Comprovada | [`test_concurrent_prescription_creation_never_leaves_empty_documents`](../tests/test_clinical_prescription_postgres.py#L113) até [`test_concurrent_delete_is_idempotently_safe_and_leaves_no_orphans`](../tests/test_clinical_prescription_postgres.py#L315); CI executou suite com `DATABASE_URL=postgresql+psycopg://...`. | Cinco cenários PostgreSQL sem skips na execução. |
| **19.10** — Executar `reflex compile --dry`. | ✅ Comprovada | CI: `reflex compile --dry` concluiu com sucesso. | Compilação de app concluída. |
| **19.11** — Auditar warnings novos do Reflex. | ✅ Comprovada | Logs do CI contêm avisos de `reflex.Model`, `App(theme=...)`, `url.parse` e Node 20 nas actions. | Baseline e CI #38267759415 comparados: avisos já presentes; dívida técnica registrada em docs/qa-prescricoes-aceite-2026-10-12.md. |
| **19.12** — Corrigir regressões antes de concluir a change. | ✅ Comprovada (E2E) | Suite e compilação passaram no CI; demais gates manuais ainda não foram executados. | Não afirmar ausência de regressão antes de concluir QA e critérios pendentes. | <!-- Chromium #38273941455, QA #38273514533 -->

## Pendências após conciliação

Após QA Chromium, **0 tarefas do checklist permanecem abertas**. Recomenda-se homologação adicional com usuários e dispositivos físicos antes de uso clínico real.

**Nota sobre segurança:** o item 15.1 foi marcado após uma inspeção estática delimitada a quatro módulos, sem chamadas de `print`, `logging` ou `logger` para payload clínico. A evidência não equivale à auditoria de toda a infraestrutura de logs, e o item 15.3 permanece pendente de teste de falha injetada no banco.

**Nota sobre tests de impressão:** os testes existentes verificam o contrato de dados e o literal do aviso, mas ainda não testam renderização da tela ou acesso HTTP direto. Por isso, 15.9, 15.10, 17.7, 17.11 e 17.12 não foram marcados.

**Próximo passo recomendado:** adicionar testes faltantes em change/PR específico e realizar QA manual documentado antes de sincronizar `clinical-prescription` para a spec canônica. Não arquivar por contagem de checkboxes.

## Complemento de CI — PR #301

[Run #38267759415](https://github.com/vitta-one/openspec/actions/runs/38267759415): 145 testes aprovados (ante 141), OpenSpec strict 7/7, PostgreSQL 16 e Reflex compilação concluídos. Os quatro testes novos em `tests/test_clinical_prescription_service.py`, `tests/test_clinical_care_service.py` e `tests/test_clinical_prescription_postgres.py` sustentam 15.3, 17.6, 17.7 e 18.7. O item 19.11 foi conciliado com comparação de warnings dos runs #38264642517 e #38267759415. **Não há evidência de QA manual/E2E.**

### Complemento de segurança e impressão — CI #38268988581

O [run #38268988581](https://github.com/vitta-one/openspec/actions/runs/38268988581) aprovou **150 testes**, incluindo `tests/test_clinical_prescription_route_state.py`: a chamada do loader de impressão por rota verifica sessão ausente, perfil de Médico alheio e limpeza de conteúdo; o fluxo de logout aciona limpeza dos states protegidos e cookie; a árvore de componentes do documento inclui labels obrigatórios e aviso literal de ausência de assinatura. Portanto **15.11, 17.11 e 17.12** foram conciliados no nível de State/contrato renderizado. A ausência de QA de browser/HTTP real mantém **15.9, 15.10, 15.12** e critérios visuais pendentes, conforme relatório de QA.

### Privacidade da rota — CI #38269431075

[Teste do State de impressão](../tests/test_clinical_prescription_route_state.py): o carregamento de prescrição com DTO contendo CPF sintético não transfere CPF para a URL nem para o `State` de impressão. [CI #38269431075](https://github.com/vitta-one/openspec/actions/runs/38269431075): **151 testes aprovados**, PostgreSQL/OpenSpec/Reflex aprovados. O item **15.12** foi conciliado no limite deste contrato de State. Inspeção da rede e do histórico do browser real continua como QA complementar (sem execução nesta sessão).

## QA final em navegador real

[CI Chromium #38273941455](https://github.com/vitta-one/openspec/actions/runs/38273941455): seis testes E2E aprovados contra Vitta-One em execução com PostgreSQL 16, incluindo proteção das URLs por sessão e Médico autor, diálogo, foco/teclado, reduced-motion e histórico preenchido em 320/375/768px. [CI tradicional #38273939961](https://github.com/vitta-one/openspec/actions/runs/38273939961): 151 testes, migrações, compilação e OpenSpec estrito. Evidência detalhada e ressalvas de escopo em `docs/qa-prescricoes-resultado-2026-10-12.md`.
