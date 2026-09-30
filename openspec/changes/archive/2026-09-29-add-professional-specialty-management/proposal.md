## Why

O Vitta-One já possui autenticação/RBAC e o primeiro fluxo operacional de paciente/fila, mas ainda não possui o conceito persistente de profissional da clínica nem especialidades administráveis. Isso bloqueia a próxima etapa do fluxo principal do domínio, porque uma Consulta precisa estar relacionada a um profissional e a futura agenda precisa conhecer quais profissionais existem.

Esta change cria a base administrativa de profissionais e especialidades sem antecipar agenda, disponibilidade, agendamento ou transições de Consulta.

## What Changes

- Permitir que o Administrador cadastre, consulte, edite e desative especialidades.
- Permitir que o Administrador cadastre, consulte, edite e desative profissionais.
- Registrar um identificador profissional único por profissional, sem fixar o sistema a um conselho específico nesta etapa.
- Permitir que um profissional possua uma ou mais especialidades e que uma especialidade esteja associada a vários profissionais.
- Permitir vínculo opcional de um profissional a exatamente uma conta local com role `MEDICO`, sem criar ou alterar credenciais nesta capability.
- Impedir associação de profissional a especialidade inativa.
- Impedir vínculo de profissional a conta que não possua role `MEDICO`.
- Preservar registros por desativação lógica em vez de exclusão física.
- Evoluir `/admin` de shell para uma área operacional de gestão de profissionais e especialidades, mantendo autorização server-side, acessibilidade e responsividade.

## Capabilities

### New Capabilities

- `professional-specialty-management`: cadastro, edição, consulta, desativação e associação entre profissionais, especialidades e, opcionalmente, uma identidade médica local.

### Modified Capabilities

Nenhuma capability existente precisa ter comportamento alterado. A capability `access-control` já permite que painéis protegidos hospedem funcionalidades definidas por capabilities específicas.

## Out of Scope

- criação, edição de senha ou administração completa de contas de usuário;
- convite, redefinição de senha ou MFA;
- agenda e horários de disponibilidade;
- agendamento, reagendamento, confirmação ou cancelamento de Consulta;
- prevenção de conflito de horário;
- fila de atendimento e suas prioridades;
- atendimento clínico, prontuário, diagnóstico, prescrição ou exames;
- integração com ZapSign, Cloudinary ou Asaas;
- dashboards gerenciais.

## Impact

- Introduz modelos persistentes de Profissional, Especialidade e associação profissional-especialidade.
- Adiciona vínculo opcional do profissional com `auth_users` limitado a contas de role `MEDICO`.
- Torna o painel administrativo funcional para esta capability.
- Exige migration Alembic incremental e testes de unicidade, cardinalidade, desativação e autorização.
- Cria a base necessária para uma change posterior de agenda/agendamento/Consulta.
