## Why

O cadastro médico em `/admin/profissionais` compartilha o serviço com Funcionários, mas o modal exibe seleção obrigatória de especialidades, um contorno extra nos checkboxes e ações pouco consistentes. A regra existente exige pelo menos uma especialidade, em conflito com o requisito de permitir associação posterior. O resultado é uma barreira cadastral desnecessária.

## What Changes

- Permitir criar e editar profissionais com zero, uma ou várias especialidades ativas, inclusive em ambos os pontos de entrada administrativos.
- Preservar validação, unicidade, RBAC, integridade transacional, identidade médica e onboarding já existentes.
- Tornar o modal acessível: checkbox/label alinhados, estado sem opções, ação secundária consistente, botão explícito de fechar, feedback de erros por campo e descrição fiel à entrega de e-mail.
- Mostrar o estado "Sem especialidades vinculadas" nas listas.
- Manter o usuário na listagem de profissionais quando a criação se iniciou por ela; redirecionar ao detalhe do funcionário apenas na jornada de Funcionários.
- Acrescentar testes de criação sem especialidade, remoção de vínculos e IDs inválidos.

## Capabilities

### Modified Capabilities

- `professional-specialty-management`: vínculo de especialidade opcional e consistência de formulários.

### New Capabilities

Nenhuma.

## Out of Scope

- Redesenhar a gestão de Funcionários, agenda médica ou primeiro acesso.
- Criar nova API, novos modelos ou migrations.
- Configurar Resend, alterar credenciais existentes, realizar merge ou deploy.

## Impact

UI, CSS, State, serviço de domínio, testes e delta OpenSpec. Sem migração de banco.
