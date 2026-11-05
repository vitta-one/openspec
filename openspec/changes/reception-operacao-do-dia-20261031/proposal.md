# Revisar operação do dia da Recepção

## Problema
A página `/recepcao` exibe apenas os cinco indicadores e um calendário semanal, embora o módulo `vitta_one/reception/dashboard/` já contenha tabela autorizada de consultas do dia, busca, filtro por profissional, paginação e ações contextuais. A operação principal fica inacessível no dashboard.

## Objetivo
Restabelecer a estação de operação diária com hierarquia clara, dados persistidos, ações reais e acesso condicionado à Recepcionista.

## Escopo
- Reutilizar projeção `reception_day_operations` e indicadores `reception_overview`.
- Exibir busca e filtro **somente** para a tabela de consultas do dia, explicitando o escopo global dos indicadores.
- Uma ação primária de nova consulta, usando a rota existente.
- Reutilizar os diálogos de check-in/reagendamento/cancelamento já autorizados na Agenda.
- Tratar carregamento, falha, estado vazio e paginação com dados reais.
- Atualização manual protegida de execuções simultâneas e refresh periódico já existente.
- Reaproveitar layout, tokens e componentes compartilhados.

## Fora do escopo
Sem novas rotas, endpoints, entidades, migrations, dados fictícios, regras clínicas ou mudanças de permissão. O calendário semanal permanece disponível na Agenda.

## Riscos
- Erros de compilação Reflex em controles condicionais precisam ser checados no CI.
- Fluxos de diálogo e teclado exigem homologação em Chromium.
