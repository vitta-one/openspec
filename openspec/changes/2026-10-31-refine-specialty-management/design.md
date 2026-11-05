## Context

A página `/admin/especialidades` em Reflex 0.9.10.post2 utiliza `AdminDirectoryState`, serviços transacionais e o componente compartilhado `page_header`/`breadcrumb`/`section_panel`. O dashboard usa cards resumidos de três registros, enquanto a página completa deve ter tabela.

## Decisions

1. Preservar o resumo do dashboard em cards; apenas a listagem completa usa `rx.table` (Radix) com cabeçalhos semânticos, scroll horizontal restrito ao container em mobile e status em texto.
2. Reutilizar os modais existentes para criação e edição. Não incluir campo "Tipo" ou alterar o modelo `Specialty`.
3. Filtrar no State autorizado em memória, com comparação `NFKD` somente para busca visual. A unicidade do domínio continua usando `normalize_specialty_key`.
4. Solicitar confirmação antes de ativar/desativar. O registro e sua situação são obtidos do State carregado do servidor; a mutação usa `admin_set_specialty_active`, com validação de sessão/role dentro da aplicação. Histórico de associações permanece íntegro.
5. Desabilitar ações durante submissão, rejeitar eventos duplicados e recarregar dados persistidos após sucesso; evitar página inválida após mutação.
6. Não acrescentar JavaScript, dependências, rota REST ou migration.

## Risks and mitigations

- Estado de tabela carregado em memória não substitui paginação SQL para diretórios muito grandes; manter dívida técnica.
- Mudanças concorrentes feitas por outros administradores podem ocorrer entre abertura do diálogo e confirmação; nova carga após a transação reflete a persistência.
- Confirmar compile Reflex, teclado e 320/390/768/1024/1440px em CI/QA; não arquivar sem evidência.
