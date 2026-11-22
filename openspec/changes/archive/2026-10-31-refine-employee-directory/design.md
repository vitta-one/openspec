## Decisões

1. **Fonte de dados:** `list_employee_directory` preserva a consulta protegida `require_role(ADMINISTRADOR)`; filtra-se apenas o conjunto já autorizado. O diretório mantém o escopo existente de contas Médico e Recepcionista.
2. **Nome ausente:** usar a identificação explícita “Nome não informado”, mantendo e-mail em coluna independente. Não duplicar nem alterar `display_name`.
3. **Busca e filtro:** `filter_employee_directory` aplica termo normalizado por `strip().casefold()` nos campos nome, e-mail e perfil, combinado com role restrita. Mudança de filtro retorna à primeira página.
4. **Densidade e semântica:** Radix `rx.table` no desktop, lista linear no mobile; a renderização usa os mesmos dados persistidos, sem duplicar estado. Ações identificam seu destinatário para leitores de tela.
5. **Paginação:** 10 registros por página na projeção atual de State, limite de página protegido por clamp; controles ocultos quando `total_pages == 1`. Avaliar paginação SQL se o diretório ganhar volume.
6. **Falhas:** carregar com indicador, tratar erro de leitura sem vazar dados internos, permitir retry. Sessão ausente e role inválida continuam redirecionando pelos guards existentes.

## Segurança

- Autorização de acesso ocorre no serviço e no carregamento/roteamento Reflex.
- UI de filtro não confere acesso a perfis fora da consulta autorizada.
- Não adicionar edição de role, exclusão, consulta por ID indiscriminada ou logs de dados pessoais.

## Verificação

- Testar filtro combinado, nomes ausentes, acesso negado e exclusão de contas Paciente.
- Rodar Pytest, validação OpenSpec strict, Reflex compile e QA de teclado/viewport antes de arquivar.
