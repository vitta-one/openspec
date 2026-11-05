## Why

O diretório de funcionários usa linhas em formato de cards, destaca indevidamente o e-mail para contas antigas e apresenta paginação mesmo com apenas uma página. A operação de busca e consulta precisa ser mais clara, compacta e acessível.

## What Changes

- Apresentar lista tabular de Nome, E-mail, Perfil e Ação de detalhes, com versão linear acessível em telas pequenas.
- Filtrar as identidades autorizadas por nome, e-mail e perfil, combinando pesquisa e select de perfil.
- Diferenciar ausência de nome cadastrado de um nome real, sem fabricar dados.
- Mostrar total e subtotal filtrado, oferecendo paginação apenas quando houver múltiplas páginas.
- Tratar carregamento, erro com nova tentativa, falta de registros e filtros sem resultados.
- Reutilizar cabeçalho, botão primário, select, tabela Reflex, labels, feedback e design system canônicos.

## Capabilities

### Modified Capabilities

- `access-control`: diretório administrativo somente leitura, com consultas protegidas por role e identificação clara.

### New Capabilities

Nenhuma.

## Out of Scope

- Novos perfis administrativos, edição/exclusão de identidades e permissões adicionais.
- Migração ou novos atributos de usuário: `display_name` já foi integrado pela PR #325.
- Paginação SQL: o volume atual permanece pequeno; manter limitação explícita e reavaliar ao escalar.
- Alteração do fluxo de criação e envio de credenciais; deploy e merge.

## Impact

- UI Reflex, State de Administração, apresentação do nome, testes e CSS responsivo.
- Sem alteração de banco ou migrations.
- Verificar compilação, autorização, fluxo de detalhes e viewports antes do merge.
