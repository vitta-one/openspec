## Implementação
- [x] Reutilizar operação de cadastro já compartilhada pelas jornadas administrativas.
- [x] Tornar vínculo de especialidades opcional no serviço, preservando validação de IDs ativos e deduplicação.
- [x] Reutilizar validações de nome/e-mail entre serviço e State.
- [x] Corrigir o visual de checkboxes, rótulo opcional e estado vazio.
- [x] Revisar fechamento, botões, feedback por campo e primeiro acesso no modal.
- [x] Apresentar estado textual quando profissional não tem especialidades.
- [x] Corrigir navegação pós-salvamento entre Profissionais e Funcionários.
- [x] Acrescentar testes de regressão de vínculo opcional e IDs inválidos.

## Validação e encerramento
- [ ] Executar `npx @fission-ai/openspec validate --all --strict`.
- [ ] Executar Pytest e `reflex compile --dry` em ambiente com dependências do repositório.
- [ ] Validar teclado, foco, Escape, erros e responsividade em Chromium.
- [ ] Revisar resultado da PR e arquivar apenas após homologação.
