# Design — Agenda e Check-in

## Fonte e fluxo
A rota /recepcao/agenda passa a carregar ReceptionAgendaState.load_agenda, que consulta via reception_get_agenda, já protegida por require_role(RECEPCIONISTA). O dashboard mantém sua projeção própria, mas deixa de ser carregado nesta rota. Não há API REST nova.

A projeção reception_calendar.py agrega exclusivamente consultas persistidas com horário convertido para timezone da clínica pelo serviço existente. A grade mostra até duas consultas por dia e o número restante. A tabela e os cartões usam os mesmos itens, com filtro reversível por dia e paginação de dez registros.

## Navegação e formulários
A semana é uma janela móvel inclusiva de sete dias corridos a partir de uma data inicial. As setas movem o início em exatamente sete dias; Hoje retorna ao dia atual da clínica. A data final é derivada no State e nunca fornecida separadamente pelo browser na tela Agenda. O input nativo armazena ISO, solicita locale pt-BR e o período visível é formatado dd/mm/aaaa.

Profissional e período são filtros comuns. Aplicar e limpar refazem a consulta autorizada; selecionar um dia altera apenas a lista derivada. Após criar uma consulta, a agenda retorna à semana iniciada no dia da reserva.

## Segurança, integridade e risco
Check-in continua por reception_confirm_arrival; reagendamento, cancelamento e exportação .ics continuam nos respectivos serviços autorizados. Nada no CSS ou nas permissões de visualização substitui checks server-side. Nenhum dado clínico é criado e não há mudança no schema. A leitura da agenda no SQL ainda pode carregar muitos registros; paginação SQL exige uma change separada coordenada entre a grade e a lista.

## QA
Revisar virada de mês/ano, empty state, mais de dois registros no dia, seleção/limpeza, data inválida, role negada, check-in duplicado, conflitos de reserva, desktop/mobile/teclado. Executar OpenSpec strict, Pytest, Reflex dry compile e Chromium antes de declarar concluído.
