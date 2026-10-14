## Why

A homologação real do Vitta-One revelou que o painel inicial do Administrador exibe listas inteiras de especialidades, gerando rolagem excessiva. Faltam superfícies separadas para gestão completa e os controles têm sinais de interatividade e espaçamento inconsistentes.

## What Changes

- Dashboard passa a exibir somente três especialidades e três profissionais mais recentes, consultados com limite explícito no PostgreSQL.
- Links "Ver todas" e "Ver todos" levam a páginas administrativas completas.
- Telas separadas oferecem busca, filtro ativo/inativo, paginação de apresentação e ações existentes de edição/ativação.
- Navegação em subrotas revalida autenticação e role no servidor.
- Controles interativos recebem cursor, foco visível e padding consistente.
- Preservar cadastro de profissional legado enquanto onboarding automático com Resend é especificado/implementado em change separada.

## Capabilities

### Modified Capabilities

- `professional-specialty-management`: visões resumida/completa do diretório e navegação.
- `access-control`: novas subrotas administrativas protegidas.

### New Capabilities

Nenhuma.

## Out of Scope

- Criar/enviar senhas médicas por e-mail neste primeiro incremento (capability seguinte).
- Redefinir contratos de agendamento, data/hora ou recorrência (change seguinte).
- Alterações em produção, exclusões ou migrações.
- Modificar permissões clínicas.

## Impact

- Reflex routes/pages, UI components, CSS, AuthState, DirectoryState, list services e aplicação de RBAC.
- Sem migração.
- QA de teclado e viewports 320px/375px/768px e CI obrigatórios antes de arquivar.
