## Contexto

A rota `/recepcao/pacientes/[patient_id]` permanece protegida por sessão de Recepcionista. O código atual utiliza `ReceptionQueueState`, `ReceptionAgendaState`, serviços de agenda/fila e componentes compartilhados Reflex. O perfil não representa um prontuário.

## Decisões

1. **Projeção restrita:** `patient_queue/profile.py` consulta somente paciente, consulta, profissional e metadados de fila, sem retornar sintomas ou dados de atendimento. `application.reception_get_patient_operational_summary` revalida a role antes da consulta. Apenas o CPF mascarado é enviado à UI.
2. **Separação temporal:** consultas futuras ativas têm horário >= instante atual; consultas anteriores, canceladas e concluídas aparecem no histórico. Histórico ordenado decrescente, paginado em seis linhas; futuras limitadas a oito. Histórico de fila mostra as seis movimentações encerradas mais recentes. Limites evitam listas extensas.
3. **Agendamento compartilhado:** `reception_booking_panel()` mantém um único formulário e serviço de reserva. `reception_booking_dialog()` reutiliza o painel em Dashboard, Agenda, Ficha e edição. A rota `/recepcao/agenda/nova` usa o mesmo painel por compatibilidade.
4. **Paciente fixado:** ação da ficha confere a identidade no servidor e fixa `booking_locked_patient_id`; a interface remove o controle de troca e o evento de reserva confere a correspondência antes de chamar o serviço transacional existente.
5. **Fila:** o serviço de entrada avulsa adquire lock transacional do registro de paciente antes de procurar entrada ativa e inserir. O check-in agendado conserva seus próprios serviços e regras. Sem migração e sem modificação de prioridade.
6. **Acesso ao portal:** somente a situação existente e um link para a página de edição, onde cadastro e convite já têm operações distintas. Não exibir segredo ou token.

## Segurança e recuperabilidade

IDs de rota inválidos ou inexistentes mostram estado não encontrado. Sessões ausentes ou role indevida redirecionam sem expor campos do paciente. Falhas de consulta mostram erro genérico e retorno seguro. Reserva revalida o slot com a lógica existente; a ficha atualiza após sucesso. Erros da reserva mantêm o modal para correção.

## Validação

- Testes unitários com pacientes/consultas/fila sintéticos e verificação de mascaramento, autorização e duplicidade.
- OpenSpec strict, Pytest, compilação Reflex e testes responsivos/teclado/Chromium pendentes de execução na CI/QA; não declarar aprovação sem evidência.
