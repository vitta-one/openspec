# Tarefas

## Interface
- [x] Substituir cards por tabela semântica de identidade e contato.
- [x] Reutilizar cabeçalho e botão primário compartilhado.
- [x] Exibir ação "Ver detalhes" apontando à ficha existente.
- [x] Implementar estado vazio contextual, erro persistente, loading e contagem correta.
- [x] Esconder paginação em uma página e adaptar apresentação mobile.

## Aplicação / segurança
- [x] Preservar paginação SQL e autenticação server-side da Recepção.
- [x] Alinhar a busca do diretório a nome, CPF e telefone normalizado.
- [x] Permitir limpar busca e preservar consulta aplicada no retorno.
- [x] Limpar projeção sensível e detalhes em falha de autorização.
- [x] Não criar duplicatas de cadastro, APIs REST ou migrações.

## Verificação
- [x] Adicionar regressões de projeção mínima, autorização, busca e paginação.
- [ ] Executar `python -m pytest -q` em ambiente com dependências.
- [ ] Executar `npx @fission-ai/openspec validate --all --strict`.
- [ ] Executar `reflex compile --dry`.
- [ ] Validar Chromium, teclado e responsividade em 320/390/768/1024/1440 px.
- [ ] Revisar CI e autorizar merge somente após homologação.
