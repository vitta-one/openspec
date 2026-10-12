> **Aceite final com evidências (12/10/2026):** **235/235 tarefas comprovadas no escopo acadêmico**. As 228 previamente conciliadas foram preservadas; as últimas 7 foram verificadas em **Chromium real** contra Reflex + PostgreSQL 16 descartável, com dados inteiramente fictícios: [CI E2E #38273941455](https://github.com/vitta-one/openspec/actions/runs/38273941455) (**6 testes E2E aprovados**) e [CI comum #38273939961](https://github.com/vitta-one/openspec/actions/runs/38273939961) (**151 testes Python, OpenSpec strict 7/7, migrações e compile aprovados**). Foram corrigidos retorno de foco e overflow mobile, e as capturas sintéticas foram inspecionadas para validar apresentação. Rastreabilidade em `docs/qa-prescricoes-resultado-2026-10-12.md`. **Não houve teste físico presencial em múltiplos dispositivos nem homologação humana formal; essas verificações são recomendadas antes de uso clínico real.**

## 1. Modelo e migration

- [x] 1.1 Criar modelo persistente `Prescription`.
- [x] 1.2 Adicionar FK obrigatória `clinical_care_record_id` com `RESTRICT`.
- [x] 1.3 Adicionar FK obrigatória `consultation_id` com `RESTRICT`.
- [x] 1.4 Adicionar FK obrigatória `doctor_user_id` com `RESTRICT`.
- [x] 1.5 Adicionar `general_notes`, `created_at` e `updated_at`.
- [x] 1.6 Criar modelo persistente `PrescriptionItem`.
- [x] 1.7 Adicionar FK obrigatória `prescription_id` com `ON DELETE CASCADE`.
- [x] 1.8 Adicionar `medication_or_item`, `instructions`, `notes`, `created_at` e `updated_at`.
- [x] 1.9 Adicionar índices para Prescription por ClinicalCareRecord, Consultation e Médico.
- [x] 1.10 Adicionar índices para PrescriptionItem por Prescription e criação.
- [x] 1.11 Registrar os modelos no metadata/imports do app.
- [x] 1.12 Criar migration incremental sobre `a6b3c9d2e5f1`.
- [x] 1.13 Revisar ordem correta de criação de tabelas/FKs/índices.
- [x] 1.14 Revisar downgrade removendo itens antes de Prescrições.
- [x] 1.15 Validar migration em PostgreSQL 16 descartável.

## 2. Domínio e validação

- [x] 2.1 Criar módulo `clinical_prescription` separado de State/UI.
- [x] 2.2 Definir erros funcionais de validação, autorização, transição, conflito e not-found.
- [x] 2.3 Implementar limite de 300 caracteres para medicamento/item.
- [x] 2.4 Implementar limite de 2.000 caracteres para orientação/posologia.
- [x] 2.5 Implementar limite de 2.000 caracteres para observações do item.
- [x] 2.6 Implementar limite de 4.000 caracteres para observações gerais.
- [x] 2.7 Normalizar whitespace externo sem reformatar conteúdo interno.
- [x] 2.8 Exigir medicamento/item não vazio.
- [x] 2.9 Exigir orientação/posologia não vazia.
- [x] 2.10 Permitir observações do item e gerais vazias.
- [x] 2.11 Não registrar payload clínico em erros/logs.
- [x] 2.12 Validar coerência Prescription ↔ ClinicalCareRecord ↔ Consultation.

## 3. Autorização e contexto editável

- [x] 3.1 Criar helper server-side para resolver contexto clínico autorizado do Médico.
- [x] 3.2 Revalidar sessão e role `MEDICO` na application boundary.
- [x] 3.3 Revalidar ClinicalCareRecord persistido.
- [x] 3.4 Revalidar Consultation persistida.
- [x] 3.5 Revalidar profissional vinculado à conta Médica autenticada.
- [x] 3.6 Revalidar `doctor_user_id` da Prescription.
- [x] 3.7 Exigir Consultation `EM_ANDAMENTO` para qualquer mutação.
- [x] 3.8 Rejeitar mutações em `CONCLUIDA`.
- [x] 3.9 Rejeitar mutações em `CONFIRMADA`, `CANCELADA` ou `AGENDADA`.
- [x] 3.10 Rejeitar Recepção/Financeiro/Admin normal antes de ler conteúdo prescrito.
- [x] 3.11 Rejeitar Médico diferente sem retornar dados clínicos.
- [x] 3.12 Preservar leitura imprimível pós-conclusão apenas para Médico autor.

## 4. Criação de Prescrição

- [x] 4.1 Implementar `create_prescription` com primeiro item no mesmo serviço.
- [x] 4.2 Bloquear/revalidar ClinicalCareRecord e Consultation antes da criação.
- [x] 4.3 Criar Prescription com vínculos coerentes.
- [x] 4.4 Criar primeiro PrescriptionItem válido na mesma transação.
- [x] 4.5 Garantir que item inválido impeça criação do documento.
- [x] 4.6 Garantir rollback se persistência de PrescriptionItem falhar.
- [x] 4.7 Retornar projeção sanitizada de Prescription + itens.
- [x] 4.8 Não alterar Consultation, QueueEntry nem ClinicalCareRecord durante a criação.

## 5. Itens de Prescrição

- [x] 5.1 Implementar adição de PrescriptionItem.
- [x] 5.2 Bloquear Prescription durante adição.
- [x] 5.3 Implementar edição de PrescriptionItem.
- [x] 5.4 Bloquear item alvo durante edição.
- [x] 5.5 Validar que item pertence à Prescription autorizada.
- [x] 5.6 Implementar remoção de PrescriptionItem.
- [x] 5.7 Recontar itens sob lock antes da remoção.
- [x] 5.8 Rejeitar remoção quando restar zero item persistido.
- [x] 5.9 Atualizar `updated_at` do item em edição válida.
- [x] 5.10 Atualizar `updated_at` da Prescription quando coleção de itens mudar.
- [x] 5.11 Preservar item anterior quando validação falhar.
- [x] 5.12 Converter concorrência/constraint em erro funcional seguro.

## 6. Documento de Prescrição

- [x] 6.1 Implementar edição de `general_notes`.
- [x] 6.2 Bloquear Prescription durante edição.
- [x] 6.3 Implementar exclusão explícita da Prescription em `EM_ANDAMENTO`.
- [x] 6.4 Confirmar ownership antes da exclusão.
- [x] 6.5 Excluir itens filhos pelo FK controlado.
- [x] 6.6 Rejeitar exclusão pós-conclusão.
- [x] 6.7 Listar Prescrições atuais por ClinicalCareRecord.
- [x] 6.8 Ordenar Prescrições atuais por criação/id.
- [x] 6.9 Ordenar itens por criação/id.
- [x] 6.10 Não criar coluna de status redundante na Prescription.

## 7. Histórico clínico com Prescrições

- [x] 7.1 Estender projeção `ClinicalHistoryItem` para incluir Prescrições concluídas.
- [x] 7.2 Definir DTO sanitizado de Prescription histórica.
- [x] 7.3 Definir DTO sanitizado de PrescriptionItem histórico.
- [x] 7.4 Carregar Prescrições somente para ClinicalCareRecords da página atual.
- [x] 7.5 Evitar query por Prescrição/item dentro de loop de histórico.
- [x] 7.6 Preservar paginação de 10 Atendimentos por página.
- [x] 7.7 Preservar ordenação de Atendimentos por `completed_at DESC`.
- [x] 7.8 Incluir estado vazio “Sem prescrições” quando aplicável.
- [x] 7.9 Excluir Prescrições da Consulta atual do histórico anterior.
- [x] 7.10 Preservar autorização de histórico pelo atendimento ativo do mesmo paciente.

## 8. Application boundary

- [x] 8.1 Criar operações autorizadas de listar Prescrições atuais.
- [x] 8.2 Criar operação autorizada de criar Prescrição.
- [x] 8.3 Criar operação autorizada de adicionar item.
- [x] 8.4 Criar operação autorizada de editar item.
- [x] 8.5 Criar operação autorizada de remover item.
- [x] 8.6 Criar operação autorizada de editar observações gerais.
- [x] 8.7 Criar operação autorizada de excluir Prescrição.
- [x] 8.8 Criar operação autorizada de leitura imprimível por Prescription id.
- [x] 8.9 Criar projeção somente leitura para Admin QA.
- [x] 8.10 Garantir que nenhuma operation retorne conteúdo antes do RBAC/ownership.

## 9. State Médico

- [x] 9.1 Adicionar lista de Prescrições atuais ao `DoctorQueueState`.
- [x] 9.2 Limpar Prescrições ao limpar atendimento ativo.
- [x] 9.3 Carregar Prescrições junto do Atendimento agendado ativo.
- [x] 9.4 Não carregar Prescrições para walk-in.
- [x] 9.5 Adicionar estado/dialog de nova Prescrição.
- [x] 9.6 Adicionar campos locais do primeiro item.
- [x] 9.7 Adicionar observações gerais da nova Prescrição.
- [x] 9.8 Implementar submit de criação com loading/erro/sucesso.
- [x] 9.9 Preservar valores do dialog em erro corrigível.
- [x] 9.10 Adicionar estado/dialog de adicionar item.
- [x] 9.11 Adicionar estado/dialog de editar item.
- [x] 9.12 Adicionar estado/dialog de editar observações gerais.
- [x] 9.13 Adicionar confirmação controlada de excluir Prescrição.
- [x] 9.14 Implementar remoção de item com feedback funcional.
- [x] 9.15 Atualizar lista local após cada mutação bem-sucedida.
- [x] 9.16 Adicionar flag única/flags coerentes de operação de Prescrição.
- [x] 9.17 Bloquear finalização enquanto operação de Prescrição estiver em andamento.
- [x] 9.18 Limpar dialogs/payloads de Prescrição após sucesso/finalização/logout.
- [x] 9.19 Preservar conteúdo de histórico com Prescrições paginadas.
- [x] 9.20 Não armazenar CPF ou dados de impressão desnecessários no State principal.

## 10. UI Médico — Prescrições

- [x] 10.1 Criar seção “Prescrições” entre Atendimento clínico e Histórico clínico.
- [x] 10.2 Adicionar estado vazio honesto.
- [x] 10.3 Adicionar botão “Nova prescrição”.
- [x] 10.4 Renderizar cada Prescription em card simples.
- [x] 10.5 Mostrar itens em lista legível, sem tabela densa.
- [x] 10.6 Mostrar medicamento/item como texto principal.
- [x] 10.7 Mostrar orientação/posologia imediatamente abaixo.
- [x] 10.8 Mostrar observações somente quando existirem.
- [x] 10.9 Mostrar observações gerais somente quando existirem.
- [x] 10.10 Adicionar “Adicionar item”.
- [x] 10.11 Adicionar ação de editar item.
- [x] 10.12 Adicionar ação de remover item.
- [x] 10.13 Desabilitar/remover ação de remover quando houver apenas um item.
- [x] 10.14 Adicionar ação de editar observações gerais.
- [x] 10.15 Adicionar ação “Excluir prescrição”.
- [x] 10.16 Adicionar ação “Visualizar para impressão”.
- [x] 10.17 Manter ações responsivas em uma coluna quando necessário.
- [x] 10.18 Preservar foco visível, labels e navegação por teclado.
- [x] 10.19 Não usar `window.confirm`/alert para fluxos destrutivos.
- [x] 10.20 Preservar reduced-motion e tokens visuais do produto.

## 11. Dialogs de Prescrição

- [x] 11.1 Criar dialog acessível de nova Prescrição.
- [x] 11.2 Criar campos de medicamento/item, orientação/posologia, observações e observações gerais.
- [x] 11.3 Refletir limites de caracteres no HTML sem depender só do cliente.
- [x] 11.4 Criar dialog acessível de adicionar item.
- [x] 11.5 Criar dialog acessível de editar item.
- [x] 11.6 Criar dialog acessível de editar observações gerais.
- [x] 11.7 Criar dialog de confirmação de exclusão da Prescription.
- [x] 11.8 Garantir foco inicial adequado.
- [x] 11.9 Não fechar dialog automaticamente em erro corrigível.
- [x] 11.10 Fechar/limpar payload somente em sucesso ou cancelamento explícito.

## 12. Visualização de impressão

- [x] 12.1 Definir rota/superfície Reflex protegida para Prescription.
- [x] 12.2 Revalidar sessão server-side ao abrir impressão.
- [x] 12.3 Revalidar ownership do Médico autor.
- [x] 12.4 Permitir leitura pós-conclusão ao Médico autor.
- [x] 12.5 Negar acesso direto a outro Médico.
- [x] 12.6 Negar acesso a roles incompatíveis.
- [x] 12.7 Renderizar sem sidebar/topbar.
- [x] 12.8 Exibir marca Vitta-One.
- [x] 12.9 Exibir paciente.
- [x] 12.10 Exibir profissional e registro profissional.
- [x] 12.11 Exibir data/horário da Consulta.
- [x] 12.12 Exibir todos os itens na ordem persistida.
- [x] 12.13 Exibir observações gerais quando existirem.
- [x] 12.14 Exibir aviso “Documento sem assinatura digital nesta etapa.”.
- [x] 12.15 Criar CSS `@media print` limpo.
- [x] 12.16 Ocultar controles de navegação/ação durante impressão.
- [x] 12.17 Não gerar PDF/arquivo persistido nesta change.
- [x] 12.18 Não exibir selo, QR Code ou status de assinatura.

## 13. Histórico UI

- [x] 13.1 Estender cards do histórico clínico para Prescrições.
- [x] 13.2 Mostrar quantidade de Prescrições por Atendimento quando maior que zero.
- [x] 13.3 Renderizar documentos históricos somente leitura.
- [x] 13.4 Renderizar itens históricos sem botões de mutação.
- [x] 13.5 Mostrar estado “Sem prescrições” quando vazio.
- [x] 13.6 Preservar paginação do histórico.
- [x] 13.7 Evitar expandir automaticamente grandes conteúdos.
- [x] 13.8 Manter viewport estreita sem rolagem horizontal obrigatória.

## 14. Admin QA

- [x] 14.1 Estender Atendimento ativo QA para mostrar Prescrições atuais.
- [x] 14.2 Estender histórico de paciente QA para Prescrições concluídas.
- [x] 14.3 Reutilizar projeções persistidas; não duplicar dados fake.
- [x] 14.4 Exigir `VITTA_ONE_LOCAL_ADMIN_PREVIEW=true`.
- [x] 14.5 Exigir sessão Administrador.
- [x] 14.6 Não renderizar criar/editar/remover.
- [x] 14.7 Não criar API clínica geral fora do QA.
- [x] 14.8 Limpar conteúdo de Prescrição do State quando contexto for limpo.

## 15. Segurança e privacidade

- [x] 15.1 Auditar services/application/state para ausência de logging de payload prescrito.
- [x] 15.2 Garantir que erros de validação não ecoem medicamento/posologia/observações.
- [x] 15.3 Garantir que erros de banco não exponham constraints/stack trace.
- [x] 15.4 Testar Recepcionista sem leitura/mutação clínica de Prescrição.
- [x] 15.5 Testar Financeiro sem leitura/mutação.
- [x] 15.6 Testar Administrador normal sem API geral.
- [x] 15.7 Testar Médico diferente sem leitura/mutação.
- [x] 15.8 Testar sessão ausente/expirada.
- [x] 15.9 Testar URL de impressão por outro Médico.
- [x] 15.10 Testar URL de impressão sem sessão.
- [x] 15.11 Garantir que logout limpe payloads de dialogs/state.
- [x] 15.12 Garantir que CPF não seja introduzido em URL/State de Prescrição.

## 16. Testes de domínio

- [x] 16.1 Testar criação de Prescription + primeiro item atomicamente.
- [x] 16.2 Testar primeiro item inválido sem documento vazio.
- [x] 16.3 Testar múltiplas Prescrições no mesmo ClinicalCareRecord.
- [x] 16.4 Testar múltiplos itens no mesmo documento.
- [x] 16.5 Testar limites de medicamento/item.
- [x] 16.6 Testar limites de orientação/posologia.
- [x] 16.7 Testar limites de observações do item.
- [x] 16.8 Testar limite de observações gerais.
- [x] 16.9 Testar edição de item.
- [x] 16.10 Testar item pertencente a outra Prescrição.
- [x] 16.11 Testar remoção com dois ou mais itens.
- [x] 16.12 Testar rejeição da remoção do último item.
- [x] 16.13 Testar exclusão da Prescription em `EM_ANDAMENTO`.
- [x] 16.14 Testar rejeição de exclusão pós-conclusão.
- [x] 16.15 Testar edição de observações gerais.
- [x] 16.16 Testar mutações sem alterar lifecycle.
- [x] 16.17 Testar mutação em estado diferente de `EM_ANDAMENTO`.
- [x] 16.18 Testar walk-in sem capability de Prescrição.

## 17. Testes de histórico e impressão

- [x] 17.1 Testar histórico concluído trazendo Prescrições corretas.
- [x] 17.2 Testar histórico sem Prescrição.
- [x] 17.3 Testar que Consulta atual não entra no histórico anterior.
- [x] 17.4 Testar múltiplas Prescrições no mesmo item de histórico.
- [x] 17.5 Testar ordem de documentos/itens.
- [x] 17.6 Testar que carregamento fica limitado à página atual.
- [x] 17.7 Testar impressão de Prescription ativa pelo Médico autor.
- [x] 17.8 Testar reimpressão de Prescription concluída pelo Médico autor.
- [x] 17.9 Testar negação de impressão para outro Médico.
- [x] 17.10 Testar negação de impressão para role incompatível.
- [x] 17.11 Testar conteúdo obrigatório da visualização imprimível.
- [x] 17.12 Testar presença do aviso de ausência de assinatura digital.

## 18. PostgreSQL e concorrência

- [x] 18.1 Testar criação concorrente de documentos/itens sem registro parcial.
- [x] 18.2 Testar dois saves concorrentes no mesmo PrescriptionItem.
- [x] 18.3 Testar remoção concorrente versus edição do mesmo item.
- [x] 18.4 Testar concorrência tentando remover os últimos itens.
- [x] 18.5 Testar exclusão concorrente da Prescription.
- [x] 18.6 Confirmar ausência de itens órfãos.
- [x] 18.7 Confirmar FKs/índices no PostgreSQL 16 real do CI.
- [x] 18.8 Executar migration completa do zero até a nova revisão.

## 19. Documentação e validação final

- [x] 19.1 Atualizar `docs/domain-model.md` com cardinalidades de Prescription/PrescriptionItem.
- [x] 19.2 Atualizar `docs/project-overview.md` removendo modelagem de prescrição dos pontos em aberto.
- [x] 19.3 Atualizar `UX-CONTRACT.md` com Prescrições, dialogs e impressão.
- [x] 19.4 Atualizar `DESIGN.md` somente para padrões visuais duráveis de documento imprimível.
- [x] 19.5 Atualizar README sem anunciar ZapSign como implementado.
- [x] 19.6 Validar OpenSpec strict.
- [x] 19.7 Executar migration PostgreSQL.
- [x] 19.8 Executar suíte completa.
- [x] 19.9 Executar testes concorrentes PostgreSQL.
- [x] 19.10 Executar `reflex compile --dry`.
- [x] 19.11 Auditar warnings novos do Reflex.
- [x] 19.12 Corrigir regressões antes de concluir a change.
