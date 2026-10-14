## ADDED Requirements

### Requirement: Subrotas administrativas conservam RBAC server-side
O sistema MUST validar sessão e role ADMINISTRADOR antes de disponibilizar conteúdo das rotas `/admin/especialidades` e `/admin/profissionais`, independentemente do estado da interface.

#### Scenario: Acesso sem sessão
- **WHEN** um visitante solicita diretamente uma das rotas de diretório
- **THEN** o acesso é negado e o usuário é direcionado para autenticação sem divulgar dados do diretório

#### Scenario: Acesso por outra role
- **WHEN** Médico, Recepcionista ou Financeiro solicita uma das rotas
- **THEN** a aplicação não apresenta a lista protegida e direciona para acesso negado
