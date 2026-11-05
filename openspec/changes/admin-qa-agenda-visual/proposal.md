# Visualização administrativa da agenda clínica em QA

## Problema
A página `/admin/agenda` apresenta listas truncadas aos primeiros 80 horários e consultas, sem calendário, contexto mensal ou seleção de profissional; a composição gera rolagem excessiva e pode induzir leitura equivocada do período.

## Objetivo
Permitir a inspeção de dados persistidos de disponibilidade e consultas por médico e data, com informações administrativas mínimas, em ambiente QA somente leitura.

## Escopo
- Calendário mensal compartilhado com a Administração, hoje destacado e seleção de qualquer dia do mês.
- Consulta por mês e profissional, inclusive profissionais inativos para preservar a leitura histórica.
- Detalhes de horários e estados reais do dia, contadores derivados de registros persistidos, paginação de listagens.
- Consultas do dia com horário, profissional e status, sem identificação de paciente.
- Revalidação da flag QA e role Administrador no servidor em toda recarga/consulta.

## Fora do escopo
Alterar o fluxo de gerenciamento de horários, criar/cancelar/reagendar consultas, mudar a estrutura de banco ou conceder permissões operacionais da Recepção.

## Critérios de aceite
- Datas históricas consultáveis e página inicial no dia local da clínica.
- Nenhum registro fictício, dado clínico, nome/CPF de paciente ou operação de escrita no preview.
- Período, filtro e contadores coerentes; sem lista infinita.
- Erros e sessão expirada bloqueiam acesso; interface responsiva e acessível por teclado.
