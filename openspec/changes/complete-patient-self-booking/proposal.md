# Completar jornada da recepção ao autogendamento do paciente

## Problema
O cadastro, a ativação e a visualização de consultas já existem, mas o paciente autenticado não consegue selecionar médico e reservar seu próprio horário.

## Solução
Usar o mesmo ledger e serviço transacional de agenda de recepção, com uma porta de entrada específica para PACIENTE resolvendo identidade exclusivamente pela sessão. Oferecer especialidade, médico, horário disponível, revisão e confirmação em interface Vitta-One responsiva.

## Preservar
- Cadastro operacional, consentimento explícito para convite e ativação de conta.
- Consultas da recepção, agenda e fila médica, atendimento clínico e prontuário PS.
- RBAC de dados sensíveis e histórico completo.
- Navegação, tokens visuais e idioma PT-BR.
