# Catálogo de capabilities OpenSpec — Vitta One

> Baseline auditada: `develop` em `08f87cd7c4228cc38d4a569d35483abec76f3b79`, em 22/11/2026. Os 25 contratos foram preservados sem alteração em `docs/archive/openspec-specs-2026-11-22/`; `openspec/specs/` está vazia neste corte acadêmico. O snapshot não prova homologação de integração externa.

## Objetivo e critérios

Reconciliar o contrato normativo com o monólito Python/Reflex, migrations e testes, sem alterar runtime, banco local, deploy ou permissão de produção. A especificação descreve contratos identificados no código e nas changes históricas, preservadas em `openspec/changes/archive/`; não há novas integrações previstas nesta entrega.

**Categorias de origem do snapshot:** `C` = spec previamente consolidada e revisada; `A` = recuperada de archive; `D` = sincronizada de delta anteriormente ativo, agora arquivado sem homologação externa inferida; `E` = contrato documental derivado de código.

## Matriz de rastreabilidade

| Capability | Origem | Evidência de código/modelo | Testes relacionados | Situação |
|---|---|---|---|---|
| `access-control` | C + D | `auth/{roles,service,authorization,staff_service}.py` | `test_auth_security.py`, `test_auth_service.py`, `test_admin_staff_creation.py` | cinco roles, convites e navegação revisados |
| `appointment-scheduling` | C + D | `appointment_scheduling/{service,weekly,ical_export}.py`, `models/appointment.py` | `test_appointment_scheduling_postgres.py`, `test_professional_weekly_schedule.py`, `test_ical_export.py` | slots, 45 dias, iCalendar e calendário |
| `clinical-care-record` | C + A | `clinical_care/{service,application}.py`, `models/clinical_care.py` | `test_clinical_care_service.py`, `test_walkin_clinical_journey.py` | concilia Consulta e QueueEntry avulsa |
| `clinical-prescription` | C + A | `clinical_prescription/{service,state}.py`, `models/clinical_prescription.py` | `test_clinical_prescription_service.py`, `test_clinical_prescription_postgres.py` | prescrição de episódio agendado e avulso; impressão protegida, sem assinatura eletrônica neste escopo |
| `consultation-care-lifecycle` | C | `consultation_care/{service,application}.py` | `test_consultation_care_lifecycle.py`, `test_consultation_care_postgres.py` | preservada |
| `patient-reception-queue` | C + D | `patient_queue/{service,profile,state}.py` | `test_patient_queue_postgres.py`, `test_reception_patient_profile.py` | fila, perfil e cadastro operacional |
| `professional-specialty-management` | C + D | `professional_directory/{service,state}.py`, `models/professional.py` | `test_professional_directory_service.py`, `test_specialty_management_filters.py` | cadastro, vínculo e filtros |
| `reception-operational-dashboard` | C + D | `reception/dashboard/{service,state}.py`, `admin_preview/` | `test_reception_dashboard.py`, `test_operational_dashboard_metrics.py` | métricas reais; revisão visual não concluída |
| `patient-self-booking` | A | `patient_portal/{booking,booking_state}.py` | `test_patient_self_scheduling.py` | autoagendamento autenticado |
| `doctor-workspace` | A | `doctor_workspace/state.py` | `test_doctor_workspace_state.py` | agenda/pacientes do Médico |
| `patient-portal` | A + D | `patient_portal/{service,state,activation_api}.py` | `test_patient_portal_and_role_agendas.py`, `test_patient_self_scheduling.py` | portal, convite e endereço persistido |
| `emergency-queue-clinical-care` | A | `patient_queue/`, `clinical_care/`, `models/clinical_care.py` | `test_walkin_clinical_journey.py` | episódio sem Consultation fictícia |
| `admin-qa-patient-dossier` | D | `admin_preview/{service,state}.py` | `test_admin_preview_patient_detail.py` | somente QA local |
| `clinic-settings` | D | `clinic_settings/service.py`, `models/clinic_settings.py` | `test_clinic_settings.py` | configuração com revisão/auditoria |
| `administration-dashboard` | D | `admin_dashboard/{service,state}.py` | `test_admin_directory_summary.py` | contagens persistidas |
| `operational-screen-presentation` | D | `ui/`, `assets/styles.css` | `test_operational_shell.py`, `test_ui_accessible_contrast.py` | 16 telas com aceite visual pendente |
| `appointment-email-notifications` | D | `notifications/service.py`, `appointment_scheduling/service.py` | `test_financial_notifications.py` | eventos implementados; entregabilidade externa não homologada |
| `email-delivery` | D | `notifications/{resend,service}.py`, `integration_api.py` | `test_financial_notifications.py` | worker/outbox/webhook; provedor real não homologado |
| `transactional-email` | D | `notifications/{templates,state}.py` | `test_medical_email_onboarding.py`, `test_financial_notifications.py` | templates e preferências; QA externo pendente |
| `asaas-payments` | D | `financial/{asaas,service}.py`, `integration_api.py` | `test_asaas_contract.py`, `test_integration_migrations.py` | adaptador Sandbox; homologação real pendente |
| `financial-management` | D | `financial/{application,state}.py`, `models/financial.py` | `test_asaas_contract.py` | cobrança/projeções; homologação pendente |
| `payment-notifications` | D | `notifications/service.py`, `models/notification.py` | `test_financial_notifications.py` | eventos financeiros de comunicação |
| `staff-management` | E | `auth/{staff_service,staff_state}.py` | `test_admin_staff_creation.py`, `test_employee_detail.py` | responsabilidades de equipe separadas de login |
| `patient-directory` | E | `patient_queue/{profile,service,state}.py` | `test_reception_patient_directory.py`, `test_reception_patient_profile.py` | cadastro/ficha sem leitura clínica |
| `professional-working-hours` | E | `appointment_scheduling/weekly.py` | `test_professional_weekly_schedule.py` | expediente recorrente e preservação de slots |

`C/A/D/E` são origem de documentação, **não** estado de produção. Nenhuma linha afirma que a suíte inteira foi executada nesta branch.

## Encerramento documental e rastreabilidade

- Na baseline `develop`, existiam 19 changes arquivadas e 26 ativas.
- Por solicitação explícita de encerramento de escopo, as 26 changes antigas foram transferidas para `openspec/changes/archive/` com seus arquivos e identificadores originais preservados, respeitando o prefixo de data. O repositório passa a ter **45 changes arquivadas e nenhuma change ativa**. Por decisão acadêmica posterior, as 25 specs foram movidas integralmente para `docs/archive/openspec-specs-2026-11-22/`, restando apenas `.gitkeep` em `openspec/specs/`.
- As tarefas ainda marcadas `- [ ]` permanecem exatamente no histórico arquivado: **arquivamento documental não é prova de execução nem homologação de pendências técnicas**. Nenhum checkbox foi marcado artificialmente.
- Propostas adicionais que não fazem mais parte do prazo acadêmico foram retiradas do PR, dos testes e do roadmap, sem incluir novas funcionalidades na aplicação.
- O CI anterior registrou OpenSpec strict **25/25**, PostgreSQL QA, **584 testes Python aprovados** (2 ignorados) e Reflex compile. Esta revisão deve validar novamente o snapshot via cópia temporária no CI.
- A validação de paridade visual `docs/qa/operational-screen-parity-2026-11-17.md` ainda registra revisão de equivalência visual pendente, independentemente do encerramento documental.
- As operações Asaas e Resend possuem contratos e adaptadores, mas testes locais não substituem homologação externa de pagamentos, webhooks e entrega de e-mail.

## Evidências e limites após o arquivamento

1. Confirmar `python scripts/validate_archived_openspec.py` para a versão exata da PR (OpenSpec strict sobre cópia temporária dos 25 contratos).
2. Confirmar migrations em QA descartável, Pytest, compilação Reflex e smoke HTTP no CI.
3. Preservar o histórico dos itens pendentes nos `tasks.md` movidos; não afirmar uma funcionalidade não exercitada no ambiente externo.
4. Manter revisão de autorização, contexto clínico e diferenciação entre fluxo agendado e avulso antes do uso com dados reais.
5. Preservar o snapshot dos 25 contratos separado das specs ativas; restaurar os contratos antes de mudanças futuras.

## Material para o Innovation Lab

Evidência demonstrável: uma capability pode estar implementada mas presente apenas numa change arquivada/ativa; agora existe spec canônica e rastreamento código → teste → contrato. Mostrar um cenário de agendamento, fila e atendimento para evidenciar que a documentação contém requisitos verificáveis, não só descrições de tela.

## Links

- [Snapshot arquivado de specs](https://github.com/vitta-one/openspec/tree/develop/docs/archive/openspec-specs-2026-11-22)
- [Mudanças OpenSpec](https://github.com/vitta-one/openspec/tree/develop/openspec/changes)
- [Evidências Asaas/Resend](https://github.com/vitta-one/openspec/blob/develop/docs/implementacao-asaas-resend-evidencias-2026-11-11.md)
- [QA visual](https://github.com/vitta-one/openspec/blob/develop/docs/qa/operational-screen-parity-2026-11-17.md)
