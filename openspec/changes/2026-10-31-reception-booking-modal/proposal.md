## Why

A Recepção já possui serviços autorizados para reservar Consultas, mas a interface de agendamento obriga sair da Agenda ou do dashboard e entrar em uma página separada. Isso quebra o fluxo operacional e repete a navegação para selecionar paciente e horário.

## What Changes

- Abrir um mesmo modal acessível da Agenda e do dashboard, com seleção de paciente, médico, data, horário e revisão.
- Localizar pacientes existentes por nome, CPF ou telefone, mascarando a identificação; reaproveitar o cadastro existente.
- Exibir médicos ativos, vínculos opcionais de especialidade, calendário compacto e horários reais disponíveis na janela de 45 dias, segundo timezone da clínica.
- Confirmar somente pelo serviço transacional existente, recuperar de conflitos e atualizar a Agenda e o dashboard após a reserva.
- Manter Consultas do período como superfície principal e preservar check-in, cancelamento e reagendamento.
- Preservar a rota legada como alias da Agenda com modal, sem página/formulário paralelo.

## Modified Capabilities

- `appointment-scheduling`
- `reception-operational-dashboard`

## Out of Scope

- Novos endpoints REST, entidades, migrations ou regras de duração de consulta.
- Alteração do serviço de reserva usado pelo portal do paciente.
- Check-in automático e alteração de permissão de outros perfis.
