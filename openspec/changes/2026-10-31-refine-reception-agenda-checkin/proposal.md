# Agenda e Check-in operacional da Recepção

## Problema
A agenda mistura o calendário de sete dias do dashboard com uma lista servida por outro State, criando filtros e períodos possivelmente divergentes. Dias sem consultas ocupam altura excessiva, há rolagem horizontal no mobile e faltam controles de navegação semanal.

## Objetivo
Concentrar a consulta operacional em uma única projeção autorizada, com período de sete dias, seleção de data, tabela desktop e cartões mobile, preservando o agendamento e o check-in existentes.

## Escopo
- Fonte única ReceptionAgendaState para calendário e lista, sem alterar o calendário de leitura do dashboard.
- Navegação sete dias anteriores/seguintes, retorno a hoje e seleção de período.
- Filtro por profissional, seleção reversível de dia e período com data brasileira.
- Preview de até dois registros e contagem dos demais, com lista paginada.
- Fluxo dedicado de novo agendamento e mutações existentes revalidadas no servidor.
- Feedback de erro, carregamento, sucesso e estado vazio.

## Fora do escopo
Sem novos modelos, migrations, endpoints, horários fictícios, alteração de regras de reserva ou integração de calendário externo. Paginação SQL não integra esta mudança; a listagem usa a paginação já existente sobre snapshot autorizado.

## Critérios de aceite
Ambas as visualizações refletem o mesmo recorte autorizado; sem check-in duplicado; ações acessíveis por teclado e mobile; nenhuma regressão em reservas ou fila. Compilação Reflex, Pytest, validação OpenSpec e QA Chromium devem ser confirmados antes do merge.
