# Catálogo de capabilities OpenSpec — Vitta One

> Baseline auditada: `develop` em `08f87cd7c4228cc38d4a569d35483abec76f3b79`, em 22/11/2026. Este catálogo acompanha a branch de reconciliação de specs; confirmação de comportamento depende de testes e de revisão. A existência de uma spec em `openspec/specs` não prova integração externa homologada.

## Objetivo e critérios

Reconciliar o contrato normativo com o monólito Python/Reflex, migrations e testes, sem alterar runtime, banco local, deploy ou permissão de produção. A especificação descreve comportamento do código identificado ou contrato de change existente; capacidades futuras permanecem somente em `openspec/changes`.

**Categorias:** `C` = spec previamente consolidada e revisada; `A` = recuperada de archive; `D` = sincronizada de delta ativo, sem aceite operacional integral; `E` = contrato documental derivado de código; `P` = proposta futura, **fora das specs consolidadas**.

## Matriz de rastreabilidade

| Capability | Origem | Evidência de código/modelo | Testes relacionados | Situação |
|---|---|---|---|---|
| `access-control` | C + D | `auth/{roles,service,authorization,staff_service}.py` | `test_auth_security.py`, `test_auth_service.py`, `test_admin_staff_creation.py` | cinco roles, convites e navegação revisados |
| `appointment-scheduling` | C + D | `appointment_scheduling/{service,weekly,ical_export}.py`, `models/appointment.py` | `test_appointment_scheduling_postgres.py`, `test_professional_weekly_schedule.py`, `test_ical_export.py` | slots, 45 dias, iCalendar e calendário |
| `clinical-care-record` | C + A | `clinical_care/{service,application}.py`, `models/clinical_care.py` | `test_clinical_care_service.py`, `test_walkin_clinical_journey.py` | concilia Consulta e QueueEntry avulsa |
| `clinical-prescription` | C + A | `clinical_prescription/{service,state}.py`, `models/clinical_prescription.py` | `test_clinical_prescription_service.py`, `test_clinical_prescription_postgres.py` | prescrição de episódio agendado e avulso; ZapSign ausente |
| `consultation-care-lifecycle` | C | `consultation_care/{service,application}.py` | `test_consultation_care_lifecycle.py`, `test_consultation_care_postgres.py` | preservada |
| `patient-reception-queue` | C + D | `patient_queue/{service,profile,state}.py` | `test_patient_queue_postgres.py`, `test_reception_patient_profile.py` | fila, perfil e cadastro operacional |
| `professional-specialty-management` | C + D | `professional_directory/{service,state}.py`, `models/professional.py` | `test_professional_directory_service.py`, `test_specialty_management_filters.py` | cadastro, vínculo e filtros |
| `reception-operational-dashboard` | C + D | `reception/dashboard/{service,state}.py`, `admin_preview/` | `test_reception_dashboard.py`, `test_operational_dashboard_metrics.py` | métricas reais; revisão visual não concluída |
| `patient-self-booking` | A | `patient_portal/{booking,booking_state}.py` | `test_patient_self_scheduling.py` | autoagendamento autenticado |
| `doctor-workspace` | A | `doctor_workspace/state.py` | `test_doctor_workspace_state.py` | agenda/pacientes do Médico |
| `patient-portal` | A + D | `patient_portal/{service,state,activation_api}.py` | `test_patient_portal_and_role_agendas.py`, `test_patient_self_scheduling.py` | portal, convite e endereço persistido |
| `emergency-queue-clinical-care` | A | `patient_queue/", `clinical_care/", `models/clinical_care.py` | `test_walkin_clinical_journey.py` | episódio sem Consultation fictícia |
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

## Changes e aceite

- 19 changes já estavam em `archive/` na baseline; as quatro capabilities em archive sem spec final foram recuperadas.
- 26 changes não arquivadas já existiam na `develop`; seus deltas foram incorporados às specs respectivas, **sem marcar tarefas desmarcadas como concluídas e sem arquivar changes**.
- Duas novas changes somente de planejamento: `add-examination-attachments` e `add-prescription-signature` (categorias P). Elas ainda não pertencem a `openspec/specs/`.
- `integrate-asaas-financial` e `extend-resend-email` continham tarefas de homologação não concluídas. Não presumir transações Sandbox reais, entrega Resend, DNS, endpoints públicos ou configuração de credenciais.
- `align-operational-screen-visual-parity` declara tarefas concluídas, mas `docs/qa/operational-screen-parity-2026-11-17.md` registra 0/16 de equivalência visual integral no comparativo de referências. Não confundir capturas com aprovação estética.
- A sincronização documental não altera o estado dos PRs previamente integrados. A aprovação do novo PR é uma revisão de documentação, não autorização de deploy nem merge.

## Pendências objetivas para encerramento

1. Revisar manualmente requisitos alterados frente às rotas e serviços da `develop`, especialmente guard de paciente, regras de conflito e episódios avulsos.
2. Rodar `npx @fission-ai/openspec validate --all --strict` no checkout local ou CI.
3. Rodar `python -m pytest -q`, migrações em PostgreSQL 16 descartável, `reflex compile --dry` e Chromium nas interfaces alteradas, conforme disponibilidade.
4. Reexecutar testes de Asaas/Resend em Sandbox real autorizado, com webhook público e credenciais seguras; não usar pacientes reais.
5. Resolver tarefas abertas e obter revisão de cada change antes de `archive` correspondente, preservando histórico.
6. Revisar a estratégia de modularização de `staff-management`, `patient-directory` e `professional-working-hours` para evitar contratos duplicados em evoluções posteriores.

## Material para o Innovation Lab

Evidência demonstrável: uma capability pode estar implementada mas presente apenas numa change arquivada/ativa; agora existe spec canônica e rastreamento código → teste → contrato. Mostrar um cenário de agendamento, fila e atendimento para evidenciar que a documentação contém requisitos verificáveis, não só descrições de tela.

## Links

- [Código e specs](https://github.com/vitta-one/openspec/tree/develop/openspec/specs)
- [Mudanças OpenSpec](https://github.com/vitta-one/openspec/tree/develop/openspec/changes)
- [Evidências Asaas/Resend](https://github.com/vitta-one/openspec/blob/develop/docs/implementacao-asaas-resend-evidencias-2026-11-11.md)
- [QA visual](https://github.com/vitta-one/openspec/blob/develop/docs/qa/operational-screen-parity-2026-11-17.md)
