# Auditoria de rastreabilidade OpenSpec — 11/10/2026

> **Escopo:** regularização documental em `vitta-one/openspec`, branch de origem `develop`, referência inicial `e5d5fa8eab668ac03693d060b8c9d53f530c52a4`. Não foram modificados código Python, migrações, testes ou histórico de changes. Este documento registra uma **inspeção estática**, não uma certificação de funcionamento.

## Fonte de verdade e política

- `openspec/specs/`: requisitos consolidados após sync e archive verificados.
- `openspec/changes/<change>/`: propostas, design, deltas e tarefas ainda em andamento.
- `AGENTS.md`, `openspec/config.yaml`, `docs/project-overview.md` e `docs/domain-model.md`: contratos transversais e decisões aprovadas.
- Marcar tarefa como concluída exige evidência correspondente; existir código não substitui executar testes, conferir autorização, fazer QA visual ou validar migrações.
- Não arquivar automaticamente uma change só porque todos os checkboxes estão marcados. Comparar proposta, delta, design, tarefas, código e testes antes de sincronizar; preservar requirements e scenarios anteriores ao aplicar `MODIFIED`.

## Inventário encontrado em develop

| Change ativa | Situação observada antes da regularização |
| --- | --- |
| `add-appointment-scheduling` | 62/62 tarefas marcadas; sync/archive não realizado |
| `add-consultation-care-lifecycle` | 79/79 tarefas marcadas; sync/archive não realizado |
| `add-clinical-care-record` | 118/118 tarefas marcadas; sync/archive não realizado |
| `refine-admin-patient-login-ux` | 19/19 tarefas marcadas; sync/archive não realizado |
| `add-clinical-prescription` | 0/235 tarefas marcadas apesar de implementação e testes versionados |

Havia três specs consolidadas: `access-control`, `patient-reception-queue` e `professional-specialty-management`. Havia três changes arquivadas: autenticação/RBAC, fila/paciente e diretório profissional. Isso não significa que todas as changes ativas estejam prontas para archive: é necessário validar o conteúdo e a execução.

## Regularização inicial — `add-clinical-prescription`

Os checkboxes foram conciliados apenas para itens de implementação identificáveis por inspeção estática. **173/235 tarefas** receberam marcação documental; **62/235** continuam em aberto. O significado do checklist é: *há implementação versionada identificável*, não *o requisito foi provado por testes*. Essa diferença precisa constar da revisão e da apresentação acadêmica.

### Evidências estáticas de implementação

| Tarefas | Evidências de código/documentação |
| --- | --- |
| 1.1–1.14 | `vitta_one/models/clinical_prescription.py`, `vitta_one/models/__init__.py`, `vitta_one/vitta_one.py`, `alembic/versions/b7d4e1f6a2c8_add_clinical_prescriptions.py` |
| 2.1–2.12, 3.1–3.12, 4.1–4.8, 5.1–5.12 e 6.1–6.10 | `vitta_one/clinical_prescription/service.py`, `vitta_one/clinical_prescription/application.py` |
| 7.1–7.10 e 8.1–8.10 | `vitta_one/clinical_care/service.py`, `vitta_one/clinical_prescription/service.py`, `vitta_one/clinical_prescription/application.py` |
| 9.1–9.20 | `vitta_one/patient_queue/state.py` |
| 10.1–10.17, 10.19; 11.1–11.7, 11.9–11.10 | `vitta_one/ui/queue_components.py`, `vitta_one/patient_queue/state.py` |
| 12.1–12.18 | `vitta_one/vitta_one.py`, `vitta_one/clinical_prescription/state.py`, `vitta_one/ui/prescription_components.py`, `assets/styles.css` |
| 13.1–13.7 e 14.1–14.8 | `vitta_one/ui/queue_components.py`, `vitta_one/admin_preview/state.py`, `vitta_one/clinical_prescription/application.py` |
| 19.1–19.5 | `docs/domain-model.md`, `docs/project-overview.md`, `UX-CONTRACT.md`, `DESIGN.md`, `README.md` |

**Correção de coerência documental:** `UX-CONTRACT.md` continha frase que tratava Prescrições como capability ainda futura, embora a seção de Prescrições já descrevesse a implementação. A frase foi alinhada aos modelos persistidos sem mudar requisitos ou código.

### Pendências deliberadamente abertas (62)

- **1.15 (1):** rodar/reconfirmar a migração num PostgreSQL 16 descartável.
- **10.18, 10.20, 11.8, 13.8 (4):** QA manual de teclado/foco, `prefers-reduced-motion`, foco inicial de diálogos e viewport estreita.
- **15.1–15.12 (12):** auditoria de segurança e privacidade, inclusive autorização, mensagens de erro, logout e URL de impressão.
- **16.1–16.18 (18):** executar e confirmar os cenários de domínio, não apenas observar os testes escritos.
- **17.1–17.12 (12):** executar e confirmar cenários de histórico/impressão.
- **18.1–18.8 (8):** executar testes de concorrência e migrações contra PostgreSQL real.
- **19.6–19.12 (7):** executar validação OpenSpec strict, migrations, suíte completa, compilação Reflex e conferir avisos/regressões.

Testes **existentes para executar**, sem resultado certificado nesta auditoria: `tests/test_clinical_prescription_service.py`, `tests/test_clinical_prescription_authorization.py` e `tests/test_clinical_prescription_postgres.py`. A pipeline `.github/workflows/validate-auth-foundation.yml` inclui PostgreSQL 16, OpenSpec strict, `reflex db migrate`, pytest e `reflex compile --dry`, mas **presença da pipeline não equivale a execução bem-sucedida na branch de revisão**.

## Roteiro de consolidação — sem archive antecipado

1. Revisar os deltas `MODIFIED` de `refine-admin-patient-login-ux` em conjunto com as três specs consolidadas, preservando os cenários preexistentes.
2. Validar as changes com tarefas integralmente marcadas: `add-appointment-scheduling`, `add-consultation-care-lifecycle`, `add-clinical-care-record` e `refine-admin-patient-login-ux`. Reexecutar checks de CI e verificar código/casos de aceitação. **Checkbox não é aprovação de archive.**
3. Se validadas, sincronizar e arquivar respeitando dependências: Agenda → Lifecycle → Registro clínico. O refinamento de UX deve ser sincronizado na base de capabilities correspondente, com revisão de conflitos; não depende da criação de novas capabilities clínicas.
4. Executar as 62 pendências de Prescrições. Só após aprovação, sincronizar `clinical-prescription` à spec principal e arquivar sua change.
5. Após cada sincronização, verificar que `openspec/specs/` ficou sem headers delta, sem cenários anteriores perdidos e que `openspec validate --all --strict --no-interactive` passa.

## Recomendações para o processo do time

- Na revisão de PR, exigir mapeamento **requisito → cenário → tarefa → implementação → teste** (ou exceção justificada).
- Colocar evidências de execução de testes em PR/CI; não marcar `Testar` como concluído só porque existe um arquivo de teste.
- Não editar `openspec/specs/` diretamente para antecipar uma change ativa. Consolidar por sync + archive após aceite.
- Registrar decisões em aberto como pendências, não preencher por suposição.
- Antes de cada archive, conferir tarefas, deltas, contexto da change, migrações, autenticação/roles e regressões.

## Limitações desta primeira etapa

A inspeção ocorreu por leitura dos arquivos no GitHub. **Não houve execução local** de `npx @fission-ai/openspec`, PostgreSQL, pytest, Reflex, verificação visual no navegador nem teste de acessibilidade automatizado. Os resultados desses comandos e revisões continuam necessários. Nenhuma change foi movida para `archive/` neste estágio.
