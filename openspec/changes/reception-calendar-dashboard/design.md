## Contexto

O primeiro refinamento tornou os indicadores e as pendências legíveis, mas manteve a agenda como uma lista curta. A interface deve espelhar o trabalho da Recepção: conferir o dia, identificar cada compromisso e situação, encaminhar para check-in na Agenda e acompanhar a fila.

## Dados e período

- Consultas vêm de Consultation, unidas aos nomes persistidos de Patient e Professional.
- O calendário cobre a data atual da clínica e os seis dias seguintes no timezone IANA configurado. O período é convertido para UTC pela função temporal existente.
- A consulta inclui todos os estados persistidos para que cancelamentos permaneçam visíveis. A contagem por dia inclui somente Consultations não canceladas; cancelamentos recebem rótulo próprio.
- A lista do dia selecionado usa a hora local exata de scheduled_at e preserva ordenação cronológica.
- Uma consulta AGENDADA de hoje com horário anterior a as_of pode receber o rótulo “Chegada pendente”, mesma regra já existente nas métricas e pendências.
- Como o modelo armazena somente um instante de compromisso, a UI usa linhas cronológicas com hora, sem blocos de duração, preenchimento de intervalo ou sinal de disponibilidade.

## Arquitetura

- Manter application.reception_overview como fronteira server-side da role RECEPCIONISTA; cada leitura manual revalida sessão e role.
- Substituir a projeção de cinco próximas consultas por uma única consulta da agenda de sete dias, preservando as quatro consultas SQL do dashboard.
- O State entrega sete datas acessíveis e os compromissos persistidos; a seleção local apenas troca o dia exibido, sem nova consulta nem filtro de dados enviados pelo cliente.
- Atualizar mantém a data selecionada quando ainda pertence ao período e retorna para hoje quando o período mudou.

## Hierarquia e espaçamento

- Cabeçalho mantém as ações reais: agendar, localizar/cadastrar paciente e atualizar.
- O calendário ocupa o primeiro lugar no painel, com seleção de dia, faixa de datas e link para a Agenda completa.
- Pendências de chegada e fila vêm logo depois do calendário, aproximando as ações operacionais dos horários. A fila detalha prioridades informadas; os totais aguardando e em atendimento ficam nos indicadores.
- Indicadores aparecem depois da área de ação, em duas colunas em tela estreita e três colunas a partir do breakpoint de tablet.
- Superfícies do dashboard recebem padding interno de 20 a 28 px; linhas de agenda usam separadores em vez de cartões aninhados, com espaços e foco visível consistentes.
- Em telas estreitas, a semana vira uma faixa rolável com cartões compactos; a rolagem permanece dentro do calendário e não cria overflow na página. Os botões de dia têm nome acessível, aria-pressed e foco visível.

## Segurança e limites

Não carregar sintomas, diagnóstico ou outras informações clínicas. Não confirmar chegada, reagendar, cancelar, criar compromissos nem alterar prioridade no dashboard. O link para a Agenda não presume filtro por data/consulta que a rota atual não ofereça. A consulta do calendário continua somente leitura.
