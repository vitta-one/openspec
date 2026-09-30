## 1. Configuração temporal e domínio

- [ ] 1.1 Adicionar configuração `VITTA_ONE_CLINIC_TIMEZONE` e validação de nome IANA sem fallback silencioso.
- [ ] 1.2 Implementar helpers para converter data/hora local da clínica ↔ UTC timezone-aware.
- [ ] 1.3 Definir enums/constantes fechadas para estados de slot `AVAILABLE`, `BOOKED`, `INACTIVE`.
- [ ] 1.4 Definir enum/constantes de Consulta com `AGENDADA`, `CONFIRMADA`, `EM_ANDAMENTO`, `CONCLUIDA`, `CANCELADA`.
- [ ] 1.5 Garantir que handlers desta capability só criem `AGENDADA` e só executem `AGENDADA → CANCELADA`.

## 2. Modelos e migration

- [ ] 2.1 Criar `ProfessionalAvailabilitySlot` com profissional, instante UTC, estado e timestamps.
- [ ] 2.2 Criar unicidade de profissional + instante do slot e índices de consulta por profissional/data/estado.
- [ ] 2.3 Criar `Consultation` com paciente, profissional, slot, data/hora, estado e timestamps de cancelamento.
- [ ] 2.4 Criar FKs com políticas de delete que preservem histórico clínico/operacional.
- [ ] 2.5 Criar proteção de persistência para no máximo uma Consulta não cancelada por slot.
- [ ] 2.6 Registrar novos modelos na descoberta Reflex/Alembic.
- [ ] 2.7 Gerar migration incremental sobre `c1fa18dd8731`, revisar upgrade/downgrade e validar em PostgreSQL 16 descartável.

## 3. Serviços de disponibilidade

- [ ] 3.1 Implementar criação de slot somente para profissional ativo e horário futuro.
- [ ] 3.2 Rejeitar slot duplicado com mensagem de conflito segura.
- [ ] 3.3 Implementar listagem/filtro de slots por profissional e período.
- [ ] 3.4 Implementar desativação somente de slot `AVAILABLE`.
- [ ] 3.5 Implementar reativação somente de slot `INACTIVE` ainda futuro.
- [ ] 3.6 Impedir que slot de profissional inativo aceite nova reserva sem apagar histórico existente.

## 4. Serviços de Consulta e agenda

- [ ] 4.1 Implementar projeção da agenda por profissional/período com slots e Consultas.
- [ ] 4.2 Implementar criação de Consulta exigindo paciente existente, profissional ativo e slot futuro `AVAILABLE`.
- [ ] 4.3 Reservar slot e criar Consulta `AGENDADA` no mesmo commit.
- [ ] 4.4 Implementar locking PostgreSQL do slot para impedir dupla reserva concorrente.
- [ ] 4.5 Converter violações do índice/constraint de reserva ativa em conflito de negócio seguro.
- [ ] 4.6 Implementar reagendamento apenas de Consulta `AGENDADA`.
- [ ] 4.7 Bloquear Consulta e slots em ordem determinística durante reagendamento.
- [ ] 4.8 Liberar slot anterior e reservar destino atomicamente, preservando estado anterior em qualquer falha.
- [ ] 4.9 Permitir destino de outro profissional ativo sem alterar o paciente.
- [ ] 4.10 Implementar cancelamento `AGENDADA → CANCELADA` com `cancelled_at`.
- [ ] 4.11 Devolver slot cancelado à disponibilidade quando ele continuar elegível.
- [ ] 4.12 Tornar cancelamento repetido uma operação rejeitada/idempotente sem sobrescrever o primeiro timestamp.
- [ ] 4.13 Rejeitar reagendamento/cancelamento via esta capability para `CONFIRMADA`, `EM_ANDAMENTO` e `CONCLUIDA`.

## 5. RBAC e camada de aplicação

- [ ] 5.1 Criar operações Administrador para criar/listar/ativar/desativar slots com revalidação server-side.
- [ ] 5.2 Criar operações Recepcionista para consultar agenda, agendar, reagendar e cancelar com revalidação server-side.
- [ ] 5.3 Rejeitar sessão ausente/expirada antes de retornar dados de agenda.
- [ ] 5.4 Rejeitar Médico/Financeiro em operações desta capability e Recepcionista em mutações administrativas.
- [ ] 5.5 Garantir que erros não exponham tokens, CPF completo desnecessário, stack trace ou detalhes internos de constraint.

## 6. State e UI do Administrador

- [ ] 6.1 Criar State de disponibilidade com filtros, loading, empty, success, error e busy states.
- [ ] 6.2 Adicionar ao `/admin` formulário de slot com profissional ativo e `datetime-local`.
- [ ] 6.3 Exibir slots por período com horário no timezone da clínica e estado textual.
- [ ] 6.4 Implementar desativação/reativação reversível e bloquear ação visualmente quando o slot estiver reservado.
- [ ] 6.5 Preservar valores de formulário quando validação server-side falhar.
- [ ] 6.6 Garantir layout responsivo, labels, foco visível e navegação por teclado.

## 7. State e UI da Recepção

- [ ] 7.1 Criar State de agenda com filtros de profissional/período, paciente selecionado, Consulta em edição e feedback operacional.
- [ ] 7.2 Reutilizar serviços de identidade de paciente existentes sem duplicar cadastro ou criar uma segunda tabela de pacientes.
- [ ] 7.3 Adicionar área de Agenda ao `/recepcao` sem quebrar a fila existente.
- [ ] 7.4 Exibir horários disponíveis e Consultas com estado textual, profissional, paciente e horário local da clínica.
- [ ] 7.5 Implementar fluxo acessível de agendamento de paciente em slot disponível.
- [ ] 7.6 Implementar fluxo de reagendamento com seleção do novo slot e confirmação explícita.
- [ ] 7.7 Implementar cancelamento de Consulta `AGENDADA` preservando histórico e devolvendo o slot.
- [ ] 7.8 Preservar seleção/inputs após conflito concorrente para facilitar escolha de outro horário.
- [ ] 7.9 Manter estados vazios e feedback sem dados fictícios e sem comunicar estado apenas por cor.
- [ ] 7.10 Garantir funcionamento em tela estreita sem rolagem horizontal obrigatória na tarefa principal.

## 8. Testes e validação

- [ ] 8.1 Testar timezone válido/inválido, conversão local↔UTC e rejeição de horário passado.
- [ ] 8.2 Testar criação, duplicidade, desativação e reativação de slot.
- [ ] 8.3 Testar agendamento válido e rejeições de paciente inexistente, profissional inativo e slot indisponível.
- [ ] 8.4 Testar que duas reservas concorrentes do mesmo slot produzem no máximo uma Consulta ativa.
- [ ] 8.5 Testar reagendamento válido, troca de profissional e rollback quando destino é ocupado concorrentemente.
- [ ] 8.6 Testar cancelamento, liberação do slot e preservação da Consulta cancelada no histórico.
- [ ] 8.7 Testar que Consultas em estados posteriores não são alteradas por handlers desta capability.
- [ ] 8.8 Testar RBAC das quatro roles e sessões ausente/expirada.
- [ ] 8.9 Validar índice único parcial/locking no PostgreSQL 16 real do CI.
- [ ] 8.10 Executar migration, suíte completa, OpenSpec strict e `reflex compile --dry`, corrigindo regressões antes de concluir a change.
