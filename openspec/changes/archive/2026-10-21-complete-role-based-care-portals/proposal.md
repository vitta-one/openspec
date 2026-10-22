## Por que

O Vitta-One já autentica a equipe e possui agenda, fila, atendimento e prescrição, mas o Médico não tem uma visão própria da agenda/pacientes e o paciente não consegue consultar seus compromissos. A Recepção também precisa manter o cadastro operacional e habilitar o portal de forma consentida, sem conceder acesso clínico.

## O que muda

- Adicionar a role `PACIENTE`, conta vinculada um-para-um ao cadastro e ativação por convite de uso único.
- Entregar uma agenda médica e uma lista de pacientes derivadas exclusivamente de consultas do profissional vinculado à sessão.
- Entregar portal de consulta do paciente com suas próprias consultas, médico, especialidade, status, data/hora local e endereço configurado.
- Permitir à Recepção atualizar dados operacionais e oferecer/reemitir convite após consentimento explícito.
- Preservar o histórico de datas ao reagendar uma consulta e exibi-lo de forma clara no portal.
- Configurar nome/endereço público da clínica por ambiente, sem endereço fictício.

## Capabilities

- MODIFIED: access-control
- MODIFIED: appointment-scheduling
- MODIFIED: patient-reception-queue
- ADDED: doctor-workspace
- ADDED: patient-portal

## Fora de escopo

Autoagendamento/cancelamento pelo paciente, prontuário ou prescrição no portal, busca global de pacientes pelo Médico, acesso clínico pela Recepção, associação automática por CPF/e-mail, endereço de clínica fictício, novos frameworks e qualquer migração de dados reais entre contas.
