## Why

O Vitta-One já define quatro roles operacionais distintas, mas ainda não possui um mecanismo de autenticação e sessão que permita identificar o usuário atual e aplicar essas permissões de forma segura. Como pacientes, agenda, prontuário, financeiro e demais módulos dependem de saber quem está operando o sistema, autenticação e RBAC precisam existir antes das funcionalidades de negócio.

## What Changes

- Adicionar autenticação local baseada em e-mail e senha, usando o próprio PostgreSQL do projeto.
- Criar sessão autenticada com possibilidade de restauração após recarregar a página e encerramento explícito por logout.
- Aplicar as quatro roles previstas pelo domínio: Administrador, Recepcionista, Médico e Financeiro.
- Impedir acesso a páginas, dados e ações incompatíveis com a role do usuário, com validação no lado servidor.
- Redirecionar usuários autenticados para um shell inicial de dashboard correspondente à sua role.
- Adicionar um mecanismo controlado e idempotente para bootstrap do primeiro Administrador sem credenciais padrão versionadas.
- Armazenar apenas hash seguro da senha; nunca persistir senha em texto puro.
- Não incluir nesta change cadastro público, recuperação de senha, MFA, login social, gestão completa de usuários ou qualquer módulo clínico/financeiro.

## Capabilities

### New Capabilities
- `access-control`: autenticação local, sessão, logout, identificação da role e autorização de acesso no Vitta-One.

### Modified Capabilities

Nenhuma. O projeto ainda não possui capabilities consolidadas em `openspec/specs/`.

## Impact

- Introduz o primeiro modelo persistente relacionado a usuários e autenticação no PostgreSQL.
- Cria a base de State/event handlers necessária para identidade e autorização no Reflex.
- Adiciona páginas públicas e protegidas mínimas para login e shell de dashboard.
- Exige configuração de conexão PostgreSQL e segredo(s) por variável de ambiente.
- Cria dependência arquitetural para as futuras changes de pacientes, profissionais, agenda, consultas, prontuário e financeiro.
