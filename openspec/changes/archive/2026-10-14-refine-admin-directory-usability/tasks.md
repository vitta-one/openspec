## Navegação e listagem
- [x] Criar serviços de listagem recente com LIMIT 3 e RBAC.
- [x] Criar resumo de três especialidades/profissionais com links de navegação.
- [x] Criar páginas completas para cada diretório.
- [x] Preservar edição, ativação e inativação com dados persistidos.
- [x] Implementar busca, filtro de situação e paginação inicial.
- [x] Revalidar subrotas no State/servidor.

## Design system
- [x] Corrigir cursor e foco em links e controles habilitados.
- [x] Unificar regras básicas de altura, padding e semibold de botões.
- [x] Executar revisão visual e interativa em desktop/tablet/mobile.

## Validação
- [x] Acrescentar testes de resumo, RBAC e paginação.
- [x] Confirmar fluxos de criação/edição após a refatoração.
- [x] Executar OpenSpec strict, Pytest completo e `reflex compile --dry` no CI.
- [x] Verificar cenário real com teclado e telas 320/375/768px.
- [x] Sync/archive somente após aprovação dos gates.

### Evidência de encerramento (2026-10-14)

- Código integrado à `develop` via PR #305.
- Gates automatizados: OpenSpec 10/10, Pytest 179 aprovados em PostgreSQL 16 descartável; Chromium com viewports 320/375/768 e fluxos de diretório/primeiro acesso/agenda.
- Requisitos sincronizados com `openspec/specs/` antes do arquivamento.
- Integração de e-mail real e homologação manual do Hackintosh são verificações de ambiente separadas, não comprovadas por estes testes.
