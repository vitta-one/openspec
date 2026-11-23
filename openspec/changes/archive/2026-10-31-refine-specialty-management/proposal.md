## Why

A página completa de especialidades apresenta cada registro em um card alto, com retorno isolado e ações inconsistentes. A inativação é executada imediatamente, mesmo tendo efeito sobre novas associações profissionais. O diretório já dispõe de autenticação, persistência, normalização, modais e paginação; precisamos ajustar a experiência sem introduzir entidades ou integrações.

## What Changes

- Especialidades em tabela semântica compacta, com nome, situação textual e ações alinhadas.
- Breadcrumb administrativo no lugar do link solto de retorno.
- Busca por nome sem distinção entre caixa e acentuação, combinada com situação, contagem real e limpeza de filtros.
- Estados vazios distintos para ausência de registros e ausência de resultados filtrados.
- Confirmação acessível para ativação/inativação; a mutação só ocorre após confirmação e autorização no servidor.
- Prevenção de duplo envio nos eventos de criação, edição e alteração de situação.

## Capabilities

### Modified Capabilities
- `professional-specialty-management`: gestão operacional de especialidades e confirmação de mudança de situação.

### New Capabilities
Nenhuma.

## Out of Scope

- Campo "Tipo", exclusão física e migrations.
- Reformulação do cadastro médico ou outras páginas administrativas.
- Paginação SQL para diretórios muito grandes, interfaces clínicas e integrações externas.

## Impact

- `vitta_one/ui/admin_directory_components.py`
- `vitta_one/professional_directory/state.py`
- Testes de filtro e cenários OpenSpec.
- As regras de persistência e RBAC atuais são reutilizadas, sem alteração no banco.
