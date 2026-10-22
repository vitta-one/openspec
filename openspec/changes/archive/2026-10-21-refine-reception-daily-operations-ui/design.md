# Design: refinamento da operação diária

## Composição

No desktop, o título, a data e a atualização real ficam à esquerda; busca, filtro de profissional e ações ficam à direita, com duas colunas para controles e uma linha de ações. A tabela segue como superfície branca, com cabeçalho suave, separadores discretos, badges existentes e linhas mais compactas. A largura da tabela permanece contida em sua região com nome acessível.

Até 672 px, a tabela é substituída visualmente por cartões com horário, paciente, telefone, profissional, especialidades, status e menu. Ambos os formatos são construídos a partir da mesma projeção server-side. O shell responsivo existente, a fonte e os tokens Vitta-One são preservados.

## Menu contextual

Usar `rx.menu` para o acionador e os itens, preservando Escape, setas, Enter/Espaço e retorno de foco providos pelo Radix. O resumo operacional é um `rx.dialog.root` irmão do menu, porque o menu fecha após uma seleção. Para consultas `AGENDADA`, os itens disponíveis são detalhes, confirmar chegada, reagendar e cancelar. Para `CONFIRMADA`, a navegação da fila de espera é permitida. Nos demais estados há apenas consulta operacional e acesso à Agenda.

Os três fluxos de transição reconsultam a Agenda protegida antes de abrir os diálogos existentes. A confirmação final continua chamando os application services atuais, que verificam role, transição, conflitos e persistência. Cancelamento continua exigindo confirmação explícita. Nenhum evento de UI concede autorização nem permite alteração clínica.

## Dados e falhas

Detalhes operacionais são atualizados a partir de um snapshot autorizado e contêm horário, identidade e contato do paciente, profissional, especialidades ativas e situação persistida. Falha de sessão limpa estado protegido e usa os redirecionamentos existentes. Se a consulta não estiver mais no snapshot filtrado, o diálogo não abre e a interface pede atualização.

Busca e filtro permanecem distintos da busca global da topbar. Trocar ou limpar filtros continua recarregando a primeira página pelo servidor. Datas e formatação continuam obedecendo ao fuso configurado da clínica; não há indicador de tempo real.

## Riscos e verificação

A árvore de componentes Radix pode afetar seleção e foco; o QA Chromium deve cobrir abertura, fechamento com Escape, ações elegíveis e abertura dos diálogos. As duas apresentações (tabela e cartão) permanecem no DOM e são alternadas por CSS, então a validação deve confirmar que só o formato visível participa da interação em cada largura. Não são necessárias migrations nem fixtures fora do PostgreSQL descartável do workflow.
