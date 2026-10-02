## 1. Modelo e migration

- [ ] 1.1 Criar modelo persistente `Prescription`.
- [ ] 1.2 Adicionar FK obrigatória `clinical_care_record_id` com `RESTRICT`.
- [ ] 1.3 Adicionar FK obrigatória `consultation_id` com `RESTRICT`.
- [ ] 1.4 Adicionar FK obrigatória `doctor_user_id` com `RESTRICT`.
- [ ] 1.5 Adicionar `general_notes`, `created_at` e `updated_at`.
- [ ] 1.6 Criar modelo persistente `PrescriptionItem`.
- [ ] 1.7 Adicionar FK obrigatória `prescription_id` com `ON DELETE CASCADE`.
- [ ] 1.8 Adicionar `medication_or_item`, `instructions`, `notes`, `created_at` e `updated_at`.
- [ ] 1.9 Adicionar índices para Prescription por ClinicalCareRecord, Consultation e Médico.
- [ ] 1.10 Adicionar índices para PrescriptionItem por Prescription e criação.
- [ ] 1.11 Registrar os modelos no metadata/imports do app.
- [ ] 1.12 Criar migration incremental sobre `a6b3c9d2e5f1`.
- [ ] 1.13 Revisar ordem correta de criação de tabelas/FKs/índices.
- [ ] 1.14 Revisar downgrade removendo itens antes de Prescrições.
- [ ] 1.15 Validar migration em PostgreSQL 16 descartável.

## 2. Domínio e validação

- [ ] 2.1 Criar módulo `clinical_prescription` separado de State/UI.
- [ ] 2.2 Definir erros funcionais de validação, autorização, transição, conflito e not-found.
- [ ] 2.3 Implementar limite de 300 caracteres para medicamento/item.
- [ ] 2.4 Implementar limite de 2.000 caracteres para orientação/posologia.
- [ ] 2.5 Implementar limite de 2.000 caracteres para observações do item.
- [ ] 2.6 Implementar limite de 4.000 caracteres para observações gerais.
- [ ] 2.7 Normalizar whitespace externo sem reformatar conteúdo interno.
- [ ] 2.8 Exigir medicamento/item não vazio.
- [ ] 2.9 Exigir orientação/posologia não vazia.
- [ ] 2.10 Permitir observações do item e gerais vazias.
- [ ] 2.11 Não registrar payload clínico em erros/logs.
- [ ] 2.12 Validar coerência Prescription ↔ ClinicalCareRecord ↔ Consultation.

## 3. Autorização e contexto editável

- [ ] 3.1 Criar helper server-side para resolver contexto clínico autorizado do Médico.
- [ ] 3.2 Revalidar sessão e role `MEDICO` na application boundary.
- [ ] 3.3 Revalidar ClinicalCareRecord persistido.
- [ ] 3.4 Revalidar Consultation persistida.
- [ ] 3.5 Revalidar profissional vinculado à conta Médica autenticada.
- [ ] 3.6 Revalidar `doctor_user_id` da Prescription.
- [ ] 3.7 Exigir Consultation `EM_ANDAMENTO` para qualquer mutação.
- [ ] 3.8 Rejeitar mutações em `CONCLUIDA`.
- [ ] 3.9 Rejeitar mutações em `CONFIRMADA`, `CANCELADA` ou `AGENDADA`.
- [ ] 3.10 Rejeitar Recepção/Financeiro/Admin normal antes de ler conteúdo prescrito.
- [ ] 3.11 Rejeitar Médico diferente sem retornar dados clínicos.
- [ ] 3.12 Preservar leitura imprimível pós-conclusão apenas para Médico autor.

## 4. Criação de Prescrição

- [ ] 4.1 Implementar `create_prescription` com primeiro item no mesmo serviço.
- [ ] 4.2 Bloquear/revalidar ClinicalCareRecord e Consultation antes da criação.
- [ ] 4.3 Criar Prescription com vínculos coerentes.
- [ ] 4.4 Criar primeiro PrescriptionItem válido na mesma transação.
- [ ] 4.5 Garantir que item inválido impeça criação do documento.
- [ ] 4.6 Garantir rollback se persistência de PrescriptionItem falhar.
- [ ] 4.7 Retornar projeção sanitizada de Prescription + itens.
- [ ] 4.8 Não alterar Consultation, QueueEntry nem ClinicalCareRecord durante a criação.

## 5. Itens de Prescrição

- [ ] 5.1 Implementar adição de PrescriptionItem.
- [ ] 5.2 Bloquear Prescription durante adição.
- [ ] 5.3 Implementar edição de PrescriptionItem.
- [ ] 5.4 Bloquear item alvo durante edição.
- [ ] 5.5 Validar que item pertence à Prescription autorizada.
- [ ] 5.6 Implementar remoção de PrescriptionItem.
- [ ] 5.7 Recontar itens sob lock antes da remoção.
- [ ] 5.8 Rejeitar remoção quando restar zero item persistido.
- [ ] 5.9 Atualizar `updated_at` do item em edição válida.
- [ ] 5.10 Atualizar `updated_at` da Prescription quando coleção de itens mudar.
- [ ] 5.11 Preservar item anterior quando validação falhar.
- [ ] 5.12 Converter concorrência/constraint em erro funcional seguro.

## 6. Documento de Prescrição

- [ ] 6.1 Implementar edição de `general_notes`.
- [ ] 6.2 Bloquear Prescription durante edição.
- [ ] 6.3 Implementar exclusão explícita da Prescription em `EM_ANDAMENTO`.
- [ ] 6.4 Confirmar ownership antes da exclusão.
- [ ] 6.5 Excluir itens filhos pelo FK controlado.
- [ ] 6.6 Rejeitar exclusão pós-conclusão.
- [ ] 6.7 Listar Prescrições atuais por ClinicalCareRecord.
- [ ] 6.8 Ordenar Prescrições atuais por criação/id.
- [ ] 6.9 Ordenar itens por criação/id.
- [ ] 6.10 Não criar coluna de status redundante na Prescription.

## 7. Histórico clínico com Prescrições

- [ ] 7.1 Estender projeção `ClinicalHistoryItem` para incluir Prescrições concluídas.
- [ ] 7.2 Definir DTO sanitizado de Prescription histórica.
- [ ] 7.3 Definir DTO sanitizado de PrescriptionItem histórico.
- [ ] 7.4 Carregar Prescrições somente para ClinicalCareRecords da página atual.
- [ ] 7.5 Evitar query por Prescrição/item dentro de loop de histórico.
- [ ] 7.6 Preservar paginação de 10 Atendimentos por página.
- [ ] 7.7 Preservar ordenação de Atendimentos por `completed_at DESC`.
- [ ] 7.8 Incluir estado vazio “Sem prescrições” quando aplicável.
- [ ] 7.9 Excluir Prescrições da Consulta atual do histórico anterior.
- [ ] 7.10 Preservar autorização de histórico pelo atendimento ativo do mesmo paciente.

## 8. Application boundary

- [ ] 8.1 Criar operações autorizadas de listar Prescrições atuais.
- [ ] 8.2 Criar operação autorizada de criar Prescrição.
- [ ] 8.3 Criar operação autorizada de adicionar item.
- [ ] 8.4 Criar operação autorizada de editar item.
- [ ] 8.5 Criar operação autorizada de remover item.
- [ ] 8.6 Criar operação autorizada de editar observações gerais.
- [ ] 8.7 Criar operação autorizada de excluir Prescrição.
- [ ] 8.8 Criar operação autorizada de leitura imprimível por Prescription id.
- [ ] 8.9 Criar projeção somente leitura para Admin QA.
- [ ] 8.10 Garantir que nenhuma operation retorne conteúdo antes do RBAC/ownership.

## 9. State Médico

- [ ] 9.1 Adicionar lista de Prescrições atuais ao `DoctorQueueState`.
- [ ] 9.2 Limpar Prescrições ao limpar atendimento ativo.
- [ ] 9.3 Carregar Prescrições junto do Atendimento agendado ativo.
- [ ] 9.4 Não carregar Prescrições para walk-in.
- [ ] 9.5 Adicionar estado/dialog de nova Prescrição.
- [ ] 9.6 Adicionar campos locais do primeiro item.
- [ ] 9.7 Adicionar observações gerais da nova Prescrição.
- [ ] 9.8 Implementar submit de criação com loading/erro/sucesso.
- [ ] 9.9 Preservar valores do dialog em erro corrigível.
- [ ] 9.10 Adicionar estado/dialog de adicionar item.
- [ ] 9.11 Adicionar estado/dialog de editar item.
- [ ] 9.12 Adicionar estado/dialog de editar observações gerais.
- [ ] 9.13 Adicionar confirmação controlada de excluir Prescrição.
- [ ] 9.14 Implementar remoção de item com feedback funcional.
- [ ] 9.15 Atualizar lista local após cada mutação bem-sucedida.
- [ ] 9.16 Adicionar flag única/flags coerentes de operação de Prescrição.
- [ ] 9.17 Bloquear finalização enquanto operação de Prescrição estiver em andamento.
- [ ] 9.18 Limpar dialogs/payloads de Prescrição após sucesso/finalização/logout.
- [ ] 9.19 Preservar conteúdo de histórico com Prescrições paginadas.
- [ ] 9.20 Não armazenar CPF ou dados de impressão desnecessários no State principal.

## 10. UI Médico — Prescrições

- [ ] 10.1 Criar seção “Prescrições” entre Atendimento clínico e Histórico clínico.
- [ ] 10.2 Adicionar estado vazio honesto.
- [ ] 10.3 Adicionar botão “Nova prescrição”.
- [ ] 10.4 Renderizar cada Prescription em card simples.
- [ ] 10.5 Mostrar itens em lista legível, sem tabela densa.
- [ ] 10.6 Mostrar medicamento/item como texto principal.
- [ ] 10.7 Mostrar orientação/posologia imediatamente abaixo.
- [ ] 10.8 Mostrar observações somente quando existirem.
- [ ] 10.9 Mostrar observações gerais somente quando existirem.
- [ ] 10.10 Adicionar “Adicionar item”.
- [ ] 10.11 Adicionar ação de editar item.
- [ ] 10.12 Adicionar ação de remover item.
- [ ] 10.13 Desabilitar/remover ação de remover quando houver apenas um item.
- [ ] 10.14 Adicionar ação de editar observações gerais.
- [ ] 10.15 Adicionar ação “Excluir prescrição”.
- [ ] 10.16 Adicionar ação “Visualizar para impressão”.
- [ ] 10.17 Manter ações responsivas em uma coluna quando necessário.
- [ ] 10.18 Preservar foco visível, labels e navegação por teclado.
- [ ] 10.19 Não usar `window.confirm`/alert para fluxos destrutivos.
- [ ] 10.20 Preservar reduced-motion e tokens visuais do produto.

## 11. Dialogs de Prescrição

- [ ] 11.1 Criar dialog acessível de nova Prescrição.
- [ ] 11.2 Criar campos de medicamento/item, orientação/posologia, observações e observações gerais.
- [ ] 11.3 Refletir limites de caracteres no HTML sem depender só do cliente.
- [ ] 11.4 Criar dialog acessível de adicionar item.
- [ ] 11.5 Criar dialog acessível de editar item.
- [ ] 11.6 Criar dialog acessível de editar observações gerais.
- [ ] 11.7 Criar dialog de confirmação de exclusão da Prescription.
- [ ] 11.8 Garantir foco inicial adequado.
- [ ] 11.9 Não fechar dialog automaticamente em erro corrigível.
- [ ] 11.10 Fechar/limpar payload somente em sucesso ou cancelamento explícito.

## 12. Visualização de impressão

- [ ] 12.1 Definir rota/superfície Reflex protegida para Prescription.
- [ ] 12.2 Revalidar sessão server-side ao abrir impressão.
- [ ] 12.3 Revalidar ownership do Médico autor.
- [ ] 12.4 Permitir leitura pós-conclusão ao Médico autor.
- [ ] 12.5 Negar acesso direto a outro Médico.
- [ ] 12.6 Negar acesso a roles incompatíveis.
- [ ] 12.7 Renderizar sem sidebar/topbar.
- [ ] 12.8 Exibir marca Vitta-One.
- [ ] 12.9 Exibir paciente.
- [ ] 12.10 Exibir profissional e registro profissional.
- [ ] 12.11 Exibir data/horário da Consulta.
- [ ] 12.12 Exibir todos os itens na ordem persistida.
- [ ] 12.13 Exibir observações gerais quando existirem.
- [ ] 12.14 Exibir aviso “Documento sem assinatura digital nesta etapa.”.
- [ ] 12.15 Criar CSS `@media print` limpo.
- [ ] 12.16 Ocultar controles de navegação/ação durante impressão.
- [ ] 12.17 Não gerar PDF/arquivo persistido nesta change.
- [ ] 12.18 Não exibir selo, QR Code ou status de assinatura.

## 13. Histórico UI

- [ ] 13.1 Estender cards do histórico clínico para Prescrições.
- [ ] 13.2 Mostrar quantidade de Prescrições por Atendimento quando maior que zero.
- [ ] 13.3 Renderizar documentos históricos somente leitura.
- [ ] 13.4 Renderizar itens históricos sem botões de mutação.
- [ ] 13.5 Mostrar estado “Sem prescrições” quando vazio.
- [ ] 13.6 Preservar paginação do histórico.
- [ ] 13.7 Evitar expandir automaticamente grandes conteúdos.
- [ ] 13.8 Manter viewport estreita sem rolagem horizontal obrigatória.

## 14. Admin QA

- [ ] 14.1 Estender Atendimento ativo QA para mostrar Prescrições atuais.
- [ ] 14.2 Estender histórico de paciente QA para Prescrições concluídas.
- [ ] 14.3 Reutilizar projeções persistidas; não duplicar dados fake.
- [ ] 14.4 Exigir `VITTA_ONE_LOCAL_ADMIN_PREVIEW=true`.
- [ ] 14.5 Exigir sessão Administrador.
- [ ] 14.6 Não renderizar criar/editar/remover.
- [ ] 14.7 Não criar API clínica geral fora do QA.
- [ ] 14.8 Limpar conteúdo de Prescrição do State quando contexto for limpo.

## 15. Segurança e privacidade

- [ ] 15.1 Auditar services/application/state para ausência de logging de payload prescrito.
- [ ] 15.2 Garantir que erros de validação não ecoem medicamento/posologia/observações.
- [ ] 15.3 Garantir que erros de banco não exponham constraints/stack trace.
- [ ] 15.4 Testar Recepcionista sem leitura/mutação clínica de Prescrição.
- [ ] 15.5 Testar Financeiro sem leitura/mutação.
- [ ] 15.6 Testar Administrador normal sem API geral.
- [ ] 15.7 Testar Médico diferente sem leitura/mutação.
- [ ] 15.8 Testar sessão ausente/expirada.
- [ ] 15.9 Testar URL de impressão por outro Médico.
- [ ] 15.10 Testar URL de impressão sem sessão.
- [ ] 15.11 Garantir que logout limpe payloads de dialogs/state.
- [ ] 15.12 Garantir que CPF não seja introduzido em URL/State de Prescrição.

## 16. Testes de domínio

- [ ] 16.1 Testar criação de Prescription + primeiro item atomicamente.
- [ ] 16.2 Testar primeiro item inválido sem documento vazio.
- [ ] 16.3 Testar múltiplas Prescrições no mesmo ClinicalCareRecord.
- [ ] 16.4 Testar múltiplos itens no mesmo documento.
- [ ] 16.5 Testar limites de medicamento/item.
- [ ] 16.6 Testar limites de orientação/posologia.
- [ ] 16.7 Testar limites de observações do item.
- [ ] 16.8 Testar limite de observações gerais.
- [ ] 16.9 Testar edição de item.
- [ ] 16.10 Testar item pertencente a outra Prescrição.
- [ ] 16.11 Testar remoção com dois ou mais itens.
- [ ] 16.12 Testar rejeição da remoção do último item.
- [ ] 16.13 Testar exclusão da Prescription em `EM_ANDAMENTO`.
- [ ] 16.14 Testar rejeição de exclusão pós-conclusão.
- [ ] 16.15 Testar edição de observações gerais.
- [ ] 16.16 Testar mutações sem alterar lifecycle.
- [ ] 16.17 Testar mutação em estado diferente de `EM_ANDAMENTO`.
- [ ] 16.18 Testar walk-in sem capability de Prescrição.

## 17. Testes de histórico e impressão

- [ ] 17.1 Testar histórico concluído trazendo Prescrições corretas.
- [ ] 17.2 Testar histórico sem Prescrição.
- [ ] 17.3 Testar que Consulta atual não entra no histórico anterior.
- [ ] 17.4 Testar múltiplas Prescrições no mesmo item de histórico.
- [ ] 17.5 Testar ordem de documentos/itens.
- [ ] 17.6 Testar que carregamento fica limitado à página atual.
- [ ] 17.7 Testar impressão de Prescription ativa pelo Médico autor.
- [ ] 17.8 Testar reimpressão de Prescription concluída pelo Médico autor.
- [ ] 17.9 Testar negação de impressão para outro Médico.
- [ ] 17.10 Testar negação de impressão para role incompatível.
- [ ] 17.11 Testar conteúdo obrigatório da visualização imprimível.
- [ ] 17.12 Testar presença do aviso de ausência de assinatura digital.

## 18. PostgreSQL e concorrência

- [ ] 18.1 Testar criação concorrente de documentos/itens sem registro parcial.
- [ ] 18.2 Testar dois saves concorrentes no mesmo PrescriptionItem.
- [ ] 18.3 Testar remoção concorrente versus edição do mesmo item.
- [ ] 18.4 Testar concorrência tentando remover os últimos itens.
- [ ] 18.5 Testar exclusão concorrente da Prescription.
- [ ] 18.6 Confirmar ausência de itens órfãos.
- [ ] 18.7 Confirmar FKs/índices no PostgreSQL 16 real do CI.
- [ ] 18.8 Executar migration completa do zero até a nova revisão.

## 19. Documentação e validação final

- [ ] 19.1 Atualizar `docs/domain-model.md` com cardinalidades de Prescription/PrescriptionItem.
- [ ] 19.2 Atualizar `docs/project-overview.md` removendo modelagem de prescrição dos pontos em aberto.
- [ ] 19.3 Atualizar `UX-CONTRACT.md` com Prescrições, dialogs e impressão.
- [ ] 19.4 Atualizar `DESIGN.md` somente para padrões visuais duráveis de documento imprimível.
- [ ] 19.5 Atualizar README sem anunciar ZapSign como implementado.
- [ ] 19.6 Validar OpenSpec strict.
- [ ] 19.7 Executar migration PostgreSQL.
- [ ] 19.8 Executar suíte completa.
- [ ] 19.9 Executar testes concorrentes PostgreSQL.
- [ ] 19.10 Executar `reflex compile --dry`.
- [ ] 19.11 Auditar warnings novos do Reflex.
- [ ] 19.12 Corrigir regressões antes de concluir a change.
