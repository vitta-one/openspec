# Unificar o cadastro de funcionários

## Por quê

O cadastro administrativo apresenta campos de identificação e estratégias de primeiro acesso diferentes por perfil, além de largura excessiva, opções de especialidade desproporcionais e mensagens de validação pouco úteis. O contrato consolidado ainda obriga escolher uma especialidade, em conflito com a necessidade de associá-la posteriormente.

## O que muda

- Formulário único em `/admin/funcionarios/novo`, com nome, e-mail, perfil e campos específicos.
- Preservação de dados comuns ao trocar de perfil e confirmação antes de descartar dados específicos.
- Nome completo obrigatório na validação do servidor, inclusive para Recepção.
- Especialidades opcionais para médicos, inclusive edição; vínculos múltiplos sem duplicação e sem especialidades inativas novas.
- Reutilização da criação transacional e da infraestrutura atual de autenticação e e-mail; feedback distingue cadastro persistido da aceitação pelo provedor.
- Layout compactado e responsivo, controle de senha acessível, erros locais, proteção contra submissão repetida.

## Fora do escopo

- Novos perfis, integração de e-mail paralela, CRM físico, novas tabelas ou migration.
- Mudanças nas credenciais de contas já existentes.
- Merge, deploy e envio de mensagens reais no ambiente de QA.

## Compatibilidade e riscos

A PR #325 já está integrada à `develop` e fornece `auth_users.display_name`. Preservar rotas legadas, diretório e eventos médicos existentes. A alteração de especialidades obrigatórias exige cenários de regressão no domínio e nas specs.
