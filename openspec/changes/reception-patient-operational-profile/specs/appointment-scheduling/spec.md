## ADDED Requirements

### Requirement: Agendamento compartilhado a partir da ficha

A Recepção SHALL reutilizar o mesmo formulário, State e serviço transacional de agendamento a partir do dashboard, da Agenda e da Ficha, em um modal acessível. O fluxo SHALL validar sessão, paciente e slot no servidor, impedir conflitos e atualizar o contexto após reserva bem-sucedida.

#### Scenario: Agendar a partir da ficha

- **WHEN** a recepcionista abre o modal pela ficha de um paciente autorizado
- **THEN** o paciente da ficha aparece selecionado e não pode ser substituído no modal
- **AND** os horários disponíveis vêm da Agenda persistida
- **AND** a recepcionista revisa paciente, profissional, data e horário antes de confirmar
- **WHEN** a recepcionista confirma uma reserva disponível
- **THEN** a consulta é persistida pelo serviço de agendamento existente
- **AND** o modal fecha e as próximas consultas da ficha são atualizadas

#### Scenario: Reserva conflitante ou repetida

- **WHEN** uma reserva é solicitada para um horário indisponível ou já reservado
- **THEN** o serviço recusa a reserva sem duplicar registros
- **AND** o modal permanece disponível para correção, com feedback de erro

#### Scenario: Agendar pela Agenda ou dashboard

- **WHEN** a recepcionista inicia uma nova consulta pela Agenda ou dashboard
- **THEN** o mesmo modal exige seleção de paciente e horário
- **AND** a rota de agendamento preexistente permanece compatível
