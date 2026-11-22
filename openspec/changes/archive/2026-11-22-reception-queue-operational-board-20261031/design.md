# Design: fila de espera operacional

## Decisões

A tela reutiliza o shell, page_header, section_panel, priority_badge, ReceptionQueueState e serviços autorizados. A ordenação continua no banco por Vermelho, Amarelo, Verde, entrada e ID, sem ordenação pela interface.

A espera é calculada a partir do timestamp UTC persistido. A entrada usa format_clinic_datetime no fuso da clínica. Os valores são snapshots atualizados apenas ao recarregar dados ou após mutações existentes.

A busca e os filtros atuam em dados da fila já autorizados no servidor, sem serializar CPF ou sintomas na URL. O erro de consulta não é mostrado como fila vazia. Ações de reavaliação e retirada continuam no servidor e preservam o histórico.

O novo guard compartilhado bloqueia a linha Patient FOR UPDATE antes da consulta por entradas ativas, servindo tanto ao pronto atendimento como ao check-in. Entradas finalizadas ou retiradas não impedem nova chegada. Não modifica modelos, migrations nem prioridades.

A interface utiliza tabela semântica no desktop e itens compactos no mobile. Prioridade sempre tem texto; os filtros possuem label, foco e limpeza. Seguem pendentes ensaios de navegador, teclado, contraste e regressões.
