# Refinar o acompanhamento administrativo da Recepção em QA

## Problema
O preview local `/admin/recepcao` ainda informa que o agendamento não foi implementado, mistura entradas retiradas com a fila operacional, usa horário UTC em texto e não apresenta filtros e critério temporal das contagens.

## Objetivo
Permitir que o Administrador autorizado em QA acompanhe o estado real da fila, o histórico de movimentações e a agenda sem receber permissão para executar ações exclusivas da Recepção.

## Escopo
- Atualizar linguagem, vazios, erros e indicador de última leitura.
- Separar fila ativa, histórico por data da transição e consultas no intervalo local da clínica.
- Manter a ordem de prioridade já consolidada para pacientes aguardando.
- Filtrar por período, prioridade, situação e profissional da agenda.
- Revalidar flag QA, sessão e role em toda consulta; não serializar sintomas, diagnósticos ou prescrições.
- Respeitar a atualização periódica existente de 60 segundos, sem novas capacidades em tempo real.
- Manter limites explícitos de consultas e testes de acesso e privacidade.

## Fora do escopo
- Mutação da fila ou da agenda pelo Administrador.
- Nova capability de agendamento, migração de banco, alteração clínica de prioridade ou mudanças na Recepção real.
- Expor dados reais de pacientes em QA; usar somente dados sintéticos.

## Critérios de aceite
- Painel reflete dados persistidos sem mensagens técnicas desatualizadas.
- Indicadores distinguem estado atual de histórico do período.
- Falha de leitura não é exibida como ausência de consultas.
- Consulta sem autorização não retorna qualquer dado protegido.
- Padrão de datas locais, filtros, responsividade e teclado preservados.
