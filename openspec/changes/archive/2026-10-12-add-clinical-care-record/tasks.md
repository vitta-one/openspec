## 1. Modelo e migration

- [x] 1.1 Criar modelo persistente `ClinicalCareRecord`.
- [x] 1.2 Adicionar FK obrigatória e unique de `consultation_id`.
- [x] 1.3 Adicionar FK obrigatória de `patient_id`.
- [x] 1.4 Adicionar FK obrigatória de `doctor_user_id`.
- [x] 1.5 Adicionar campos `chief_complaint`, `anamnesis`, `diagnosis` e `conduct_notes`.
- [x] 1.6 Adicionar `created_at` e `updated_at` UTC.
- [x] 1.7 Adicionar índices de consulta por paciente, Médico e atualização.
- [x] 1.8 Registrar o modelo no metadata/imports usados pelas migrations.
- [x] 1.9 Criar migration incremental sobre a revisão de consultation-care-lifecycle.
- [x] 1.10 Revisar downgrade sem afetar Consulta/fila.
- [x] 1.11 Validar migration em PostgreSQL 16 descartável.

## 2. Criação atômica no início do atendimento

- [x] 2.1 Criar serviço de domínio/application para ClinicalCareRecord.
- [x] 2.2 Integrar criação ao fluxo de chamada de QueueEntry agendada.
- [x] 2.3 Criar Atendimento com `consultation_id`, `patient_id` e `doctor_user_id` corretos.
- [x] 2.4 Garantir que o Atendimento nasce com campos clínicos vazios.
- [x] 2.5 Criar o Atendimento antes do commit que confirma `EM_ANDAMENTO`.
- [x] 2.6 Rejeitar criação se já existir ClinicalCareRecord para a Consulta.
- [x] 2.7 Converter conflito de unicidade em erro funcional seguro.
- [x] 2.8 Garantir rollback integral de fila/Consulta/Atendimento se a criação falhar.
- [x] 2.9 Preservar claim/finalize de walk-in sem criar ClinicalCareRecord.

## 3. Validação e edição clínica

- [x] 3.1 Implementar limites server-side dos quatro campos.
- [x] 3.2 Normalizar somente whitespace externo sem reformatar conteúdo interno.
- [x] 3.3 Permitir campos vazios e saves parciais.
- [x] 3.4 Bloquear ClinicalCareRecord com `FOR UPDATE` durante save.
- [x] 3.5 Revalidar sessão e role Médico antes de leitura/mutação clínica.
- [x] 3.6 Revalidar que o Médico autenticado corresponde ao profissional da Consulta.
- [x] 3.7 Revalidar `doctor_user_id` persistido no ClinicalCareRecord.
- [x] 3.8 Revalidar que a Consulta está `EM_ANDAMENTO`.
- [x] 3.9 Atualizar `updated_at` somente em save válido.
- [x] 3.10 Rejeitar save após `CONCLUIDA`, `CANCELADA`, `CONFIRMADA` ou `AGENDADA`.
- [x] 3.11 Garantir que save clínico não altera estado/timestamps da fila ou Consulta.
- [x] 3.12 Não incluir textos clínicos em exceptions/logs.

## 4. Histórico clínico

- [x] 4.1 Criar projeção de histórico baseada em ClinicalCareRecord + Consultation concluída.
- [x] 4.2 Filtrar por `patient_id`.
- [x] 4.3 Ordenar por `completed_at DESC` e id da Consulta.
- [x] 4.4 Excluir Consulta atual ainda em andamento.
- [x] 4.5 Excluir registros de Consultas não concluídas.
- [x] 4.6 Implementar paginação server-side com 10 itens.
- [x] 4.7 Retornar total, página atual e total de páginas.
- [x] 4.8 Restringir leitura ao Médico com atendimento ativo do mesmo paciente.
- [x] 4.9 Rejeitar tentativa de leitura de outro paciente.
- [x] 4.10 Não criar entidade física separada de Prontuário.

## 5. State Médico

- [x] 5.1 Estender `DoctorQueueState` com snapshot do ClinicalCareRecord atual.
- [x] 5.2 Adicionar campos editáveis para queixa principal, anamnese, diagnóstico e conduta/observações.
- [x] 5.3 Adicionar snapshot persistido para detecção de alterações não salvas.
- [x] 5.4 Adicionar computed var de dirty state.
- [x] 5.5 Carregar ClinicalCareRecord ao restaurar atendimento agendado ativo.
- [x] 5.6 Não carregar formulário clínico para walk-in.
- [x] 5.7 Carregar primeira página do histórico do paciente autorizado.
- [x] 5.8 Implementar paginação anterior/próxima do histórico.
- [x] 5.9 Implementar save com loading/erro/sucesso.
- [x] 5.10 Preservar conteúdo local quando save falhar por erro corrigível.
- [x] 5.11 Atualizar snapshot e limpar dirty state após save.
- [x] 5.12 Desabilitar finalização no fluxo normal enquanto houver alterações locais não salvas.
- [x] 5.13 Limpar formulário/histórico ao finalizar atendimento.
- [x] 5.14 Limpar dados clínicos ao perder sessão/autorização.

## 6. UI Médico

- [x] 6.1 Criar seção “Atendimento clínico” abaixo do contexto operacional.
- [x] 6.2 Usar labels explícitos para os quatro campos.
- [x] 6.3 Usar textarea nativa/Reflex com resize vertical e foco visível.
- [x] 6.4 Exibir contagem/limite de caracteres quando útil sem poluir a interface.
- [x] 6.5 Adicionar ação primária “Salvar atendimento”.
- [x] 6.6 Exibir estado “Salvo” / “Alterações não salvas” em texto.
- [x] 6.7 Integrar ação existente “Finalizar atendimento” ao dirty state.
- [x] 6.8 Criar seção “Histórico clínico” somente leitura abaixo do formulário.
- [x] 6.9 Renderizar histórico em cards/accordion simples e responsivo.
- [x] 6.10 Mostrar data, profissional e quatro áreas clínicas sem inventar dados.
- [x] 6.11 Adicionar paginação simples do histórico.
- [x] 6.12 Manter uma coluna em viewport estreita.
- [x] 6.13 Preservar teclado, foco, contraste e reduced-motion.
- [x] 6.14 Manter o fluxo walk-in visualmente inalterado quanto ao ClinicalCareRecord.

## 7. Admin QA

- [x] 7.1 Criar operação/projeção somente leitura de histórico clínico para o Admin preview local.
- [x] 7.2 Exigir flag `VITTA_ONE_LOCAL_ADMIN_PREVIEW=true` e sessão Administrador.
- [x] 7.3 Integrar dados reais à seleção de paciente em `/admin/pacientes`.
- [x] 7.4 Substituir placeholder de prontuário por histórico clínico persistido quando existir.
- [x] 7.5 Manter estado vazio honesto quando não houver registros.
- [x] 7.6 Não renderizar ações de editar/salvar no Admin QA.
- [x] 7.7 Paginar histórico para evitar carga ilimitada.
- [x] 7.8 Limpar conteúdo clínico do State ao trocar/limpar paciente.

## 8. Segurança e privacidade

- [x] 8.1 Auditar handlers para não registrar payload clínico.
- [x] 8.2 Garantir que mensagens de validação não ecoem texto digitado.
- [x] 8.3 Garantir que errors de banco não exponham constraint/stack trace.
- [x] 8.4 Testar role Recepcionista sem acesso de leitura/escrita clínica.
- [x] 8.5 Testar role Administrador fora do Admin QA sem API clínica geral.
- [x] 8.6 Testar role Financeiro sem acesso clínico.
- [x] 8.7 Testar Médico diferente sem leitura/escrita do registro atual.
- [x] 8.8 Testar sessão ausente/expirada limpando dados do State.

## 9. Testes de domínio e autorização

- [x] 9.1 Testar criação automática do ClinicalCareRecord na chamada agendada.
- [x] 9.2 Testar walk-in sem criação de ClinicalCareRecord.
- [x] 9.3 Testar unicidade de um Atendimento por Consulta.
- [x] 9.4 Testar rollback da chamada quando criação do Atendimento falha.
- [x] 9.5 Testar save parcial e campos vazios.
- [x] 9.6 Testar limites dos quatro campos.
- [x] 9.7 Testar save por Médico correto em `EM_ANDAMENTO`.
- [x] 9.8 Testar save por Médico diferente.
- [x] 9.9 Testar save por role não Médica.
- [x] 9.10 Testar imutabilidade após `CONCLUIDA`.
- [x] 9.11 Testar que finalizar registro vazio continua permitido.
- [x] 9.12 Testar que save não altera lifecycle.
- [x] 9.13 Testar histórico contendo somente Consultas concluídas.
- [x] 9.14 Testar ordenação cronológica decrescente.
- [x] 9.15 Testar paginação com mais de 10 registros.
- [x] 9.16 Testar que Médico sem atendimento ativo não lê histórico.
- [x] 9.17 Testar tentativa de histórico de outro paciente.
- [x] 9.18 Testar limpeza do State após finalização/logout.

## 10. PostgreSQL e concorrência

- [x] 10.1 Testar duas chamadas concorrentes produzindo no máximo um ClinicalCareRecord.
- [x] 10.2 Testar consistência entre QueueEntry, Consultation e ClinicalCareRecord sob concorrência.
- [x] 10.3 Testar dois saves concorrentes no mesmo ClinicalCareRecord.
- [x] 10.4 Confirmar constraints/FKs/índices na migration real.
- [x] 10.5 Executar migration contra PostgreSQL 16 do CI.

## 11. Documentação e validação final

- [x] 11.1 Atualizar `docs/domain-model.md` com a cardinalidade definida de um Atendimento por Consulta.
- [x] 11.2 Atualizar `docs/project-overview.md` removendo pontos de lifecycle que já deixaram de estar em aberto.
- [x] 11.3 Atualizar `UX-CONTRACT.md` com formulário clínico, dirty state e histórico.
- [x] 11.4 Atualizar `DESIGN.md` apenas para padrões duráveis novos.
- [x] 11.5 Atualizar README com o novo fluxo Médico sem anunciar prescrição/exames.
- [x] 11.6 Validar OpenSpec com `--all --strict --no-interactive`.
- [x] 11.7 Executar suíte completa de testes.
- [x] 11.8 Executar `reflex compile --dry`.
- [x] 11.9 Corrigir regressões antes de concluir a change.
