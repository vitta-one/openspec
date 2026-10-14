## Context

Stack: Python 3.12, Reflex 0.9.10.post2, PostgreSQL 16, Radix Themes, OpenSpec. Existem sete specs consolidadas. UI de gestão em `vitta_one/ui/admin_directory_components.py` e State em `vitta_one/professional_directory/state.py`. O controle de acesso passa por `AuthState.load_protected` e `require_role`.

## Decisions

1. No dashboard, a lista recente é consultada com `created_at DESC, id DESC, LIMIT 3` por meio de operação protegida na aplicação. Nenhum fake.
2. As páginas `/admin/especialidades` e `/admin/profissionais` reutilizam os mesmos diálogos e handlers; telas não duplicam regras de domínio.
3. `AuthState.load_protected` conhece as novas rotas e grava o path autenticado; `protected_workspace` verifica rota e role. Não é preview QA: autorização Admin real.
4. Busca, filtro e paginação inicial atuam sobre dados administrativos carregados no State (10 linhas por página), evitando alteração de SQL de gestão legada neste incremento. Registrar evolução para paginação SQL de diretórios grandes, pois a página completa ainda carrega o conjunto.
5. Estilos globais para pointer/foco/botões preservam campos e controles específicos. Não adicionar ação a elementos decorativos.
6. Alterações devem conservar mesmo histórico de especialidades e profissionais, inclusive inativos.

## Risks / mitigations

- Rota sem verificação pode expor diretório: RBAC obrigatório em `AuthState` e application boundary; testar visitante e role não Admin.
- `@rx.var` e selects devem compilar com versão pinada.
- Sincronização de duas listas após mutações: reload de State; testes evitam duplicidade.
- Paginação de State para listas grandes: dívida técnica documentada; futura paginação SQL.
- CSS global não deve quebrar controles compactos; inspecionar visualmente.

## Validation

OpenSpec strict, Pytest completo PostgreSQL 16, Reflex compile e navegação real keyboard/mobile. Arquivar só quando houver evidências.
