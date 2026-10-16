# Refinar a operação diária da Recepção

## Problema

A página `/recepcao` já consulta dados persistidos, aplica filtro e paginação no servidor e respeita a role Recepcionista. A composição visual ainda separa cabeçalho e filtros, o atalho de três pontos apenas abre a Agenda sem usar a consulta selecionada, e a tabela fica larga demais em telas pequenas.

## Objetivo

Aproximar a hierarquia da tela da referência visual existente e tornar as ações frequentes da Recepção contextuais, acessíveis e consistentes com os serviços e diálogos da Agenda.

## Escopo

- Organizar título, data, busca, filtro e ações em uma faixa compacta no desktop.
- Reduzir a altura das linhas da tabela sem alterar a tipografia ou os tokens existentes.
- Exibir cartões operacionais em telas de até 672 px e manter a tabela para viewports maiores.
- Trocar o atalho genérico por menu Radix com resumo operacional e ações elegíveis por status.
- Revalidar a autorização e o estado da consulta ao abrir chegada, reagendamento e cancelamento.
- Manter detalhes limitados a dados operacionais já autorizados, sem conteúdo clínico.
- Ajustar os rótulos da navegação da Recepção e remover o indicador não verificado de saúde do sistema.
- Atualizar QA Chromium e os requisitos OpenSpec.

## Fora do escopo

- Mudanças de modelos, migrations, integrações, unidades clínicas ou regras do domínio.
- Sincronização em tempo real, notificações, ações clínicas ou atualização automática.
- Reescrita da Agenda, da fila ou da busca global de pacientes.

## Critérios de aceite

- As ações disponíveis variam conforme o estado persistido e as transições são validadas no servidor.
- O menu pode ser operado por teclado e seus fluxos usam os diálogos existentes fora da árvore do menu.
- A versão mobile oferece acesso às colunas e ações sem rolagem horizontal do documento.
- Busca, filtro, paginação server-side, shell autenticado e proteção RBAC continuam funcionando.
- Reflex compila, testes Python passam e o workflow Chromium captura desktop e mobile.
