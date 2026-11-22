# Proposta — Modais e operações de especialidades

## Problema
O formulário de cadastro e edição estava duplicado; erros de formulário eram exibidos também na página; avisos de sucesso ocupavam espaço permanente. A edição abria com o nome fornecido pela linha, e ações simultâneas podiam sobrescrever alterações mais recentes.

## Objetivo
Uniformizar os modais de `/admin/especialidades`, preservar dados digitados após erro e aumentar a segurança de edição e alteração de situação, sem mudar o domínio nem outras rotas.

## Escopo
- Formulário visual e estrutural único para cadastro e edição, com validação contextual.
- Feedback proporcional em toast após persistência, com correção do z-index já existente.
- Releitura autorizada antes de abrir a edição; verificação de estado defasado sob lock.
- Proteção contra submissões duplicadas e correção da página após mudança de filtro.
- Testes de integridade e autorização.

## Fora do escopo
- Introduzir campo "Tipo", novos modelos ou migrations.
- Apagar associações, consultas históricas ou reagendar automaticamente.
- Refatorar os fluxos de Profissionais, Funcionários e Agenda.
