## 1. OpenSpec e contrato

- [x] 1.1 Registrar deltas de access-control, professional-specialty-management e patient-reception-queue.
- [x] 1.2 Atualizar UX-CONTRACT.md com diálogos administrativos, paginação/seleção e responsivo do login.

## 2. Administração

- [x] 2.1 Adicionar estado/eventos de abertura e fechamento dos diálogos ao AdminDirectoryState.
- [x] 2.2 Reutilizar o formulário de especialidade em modal para criação e edição.
- [x] 2.3 Reutilizar o formulário de profissional em modal para criação e edição.
- [x] 2.4 Tornar listas de especialidades/profissionais o conteúdo principal e preservar feedback/loading.
- [x] 2.5 Manter desativação/reativação e autorização existentes sem alterações de domínio.

## 3. Pacientes

- [x] 3.1 Adicionar paginação local e computed vars ao AdminPreviewState.
- [x] 3.2 Resetar paginação corretamente em busca/limpeza e manter limites válidos.
- [x] 3.3 Implementar seleção simples por checkbox e limpeza explícita.
- [x] 3.4 Reestruturar patients_preview com busca no topo, lista paginada e barra contextual.
- [x] 3.5 Preservar histórico operacional e ausência de mutações no modo Admin QA.

## 4. Login e responsivo

- [x] 4.1 Centralizar geometricamente o botão de revelar/ocultar senha.
- [x] 4.2 Refinar breakpoints de largura e altura do login.
- [x] 4.3 Preservar semântica, labels, autocomplete, aria-label/aria-pressed e reduced motion.

## 5. Verificação

- [x] 5.1 Adicionar testes unitários para paginação/filtro/seleção quando aplicável.
- [ ] 5.2 Executar `python -m pytest -q`.
- [ ] 5.3 Executar `reflex compile --dry`.
- [ ] 5.4 Validar OpenSpec e registrar qualquer risco visual que exija inspeção manual.
