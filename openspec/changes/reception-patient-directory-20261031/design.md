# Design — Diretório de pacientes

## Arquitetura preservada

A rota `/recepcao/pacientes` mantém `AuthState.load_protected` e `ReceptionQueueState.load_patient_list`. O State revalida a sessão pela operação `reception_list_patient_directory`, que exige `Role.RECEPCIONISTA` antes de executar `SELECT`. A ficha usa a rota existente `/recepcao/pacientes/[patient_id]` com validação server-side de identidade.

Não criar tabelas, modelos, migrations, rotas REST ou formulário paralelo. A tela dedicada `/recepcao/pacientes/novo` e o fluxo de edição permanecem intactos.

## Comportamento

A entrada controla o texto digitado, enquanto o termo aplicado fica separado no State para não executar SQL a cada tecla. Submeter via Enter ou botão "Buscar" reinicia a página em 1. O botão "Limpar" remove o termo aplicado e retorna à primeira página; voltar da ficha preserva o último termo aplicado. O serviço SQL aplica `LIMIT/OFFSET`, ordenação estável por nome/ID e contagem real.

Nomes fazem correspondência case-insensitive com caracteres especiais de LIKE escapados; CPF e telefone usam dígitos normalizados na consulta. A projeção devolve somente ID, nome, telefone e URL da ficha, sem CPF em claro ou dados clínicos.

A tabela tem as colunas Paciente / Telefone / Ações em desktop e duas colunas em mobile; o contato passa a ser texto secundário na célula de paciente em telas estreitas. Links com nomes acessíveis substituem a seta ambígua.

## Erros, segurança e acessibilidade

Falhas de autorização limpam diretório, busca, detalhes previamente selecionados e demais dados sensíveis mantidos no State e redirecionam para login ou acesso negado. Erro inesperado limpa resultados desatualizados e apresenta mensagem persistente com tentativa de recarregar. O status e a contagem possuem `aria-live`; a tabela é semanticamente nativa, os controles possuem labels e estados de foco visível.

O backend mantém autenticação por leitura, inclusive paginação e nova busca. Dados pessoais não vão a logs, toasts técnicos ou query strings de URL. Uma pesquisa vazia lista registros paginados, e texto de pesquisa é limitado a 100 caracteres.

## Verificação

- Testar autorização, ausência de sessão, busca por nome/CPF/telefone, escapes de LIKE, projeção mínima e paginação SQL.
- Executar OpenSpec strict, Pytest e Reflex compile.
- Validar em Chromium 320/390/768/1024/1440 px, teclado e sem overflow.
- Conferir criação, retorno à lista, busca, detalhes e sessão expirada com dados sintéticos.
