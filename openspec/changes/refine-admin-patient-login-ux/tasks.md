## 1. OpenSpec e contrato

- [ ] 1.1 Registrar deltas de access-control, professional-specialty-management e patient-reception-queue.
- [ ] 1.2 Atualizar UX-CONTRACT.md com diálogos administrativos, paginação/seleção e responsivo do login.

## 2. Administração

- [ ] 2.1 Adicionar estado/eventos de abertura e fechamento dos diálogos ao AdminDirectoryState.
- [ ] 2.2 Reutilizar o formulário de especialidade em modal para criação e edição.
- [ ] 2.3 Reutilizar o formulário de profissional em modal para criação e edição.
- [ ] 2.4 Tornar listas de especialidades/profissionais o conteúdo principal e preservar feedback/loading.
- [ ] 2.5 Manter desativação/reativação e autorização existentes sem alterações de domínio.

## 3. Pacientes

- [ ] 3.1 Adicionar paginação local e computed vars ao AdminPreviewState.
- [ ] 3.2 Resetar paginação corretamente em busca/limpeza e manter limites válidos.
- [ ] 3.3 Implementar seleção simples por checkbox e limpeza explícita.
- [ ] 3.4 Reestruturar patients_preview com busca no topo, lista paginada e barra contextual.
- [ ] 3.5 Preservar histórico operacional e ausência de mutações no modo Admin QA.

## 4. Login e responsivo

- [ ] 4.1 Centralizar geometricamente o botão de revelar/ocultar senha.
- [ ] 4.2 Refinar breakpoints de largura e altura do login.
- [ ] 4.3 Preservar semântica, labels, autocomplete, aria-label/aria-pressed e reduced motion.

## 5. Verificação

- [ ] 5.1 Adicionar testes unitários para paginação/filtro/seleção quando aplicável.
- [ ] 5.2 Executar `python -m pytest -q`.
- [ ] 5.3 Executar `reflex compile --dry`.
- [ ] 5.4 Validar OpenSpec e registrar qualquer risco visual que exija inspeção manual.
