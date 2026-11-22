# appointment-scheduling Specification

## Purpose

Permitir que a clínica declare horários futuros de atendimento e que a Recepção consulte a agenda, agende, reagende e cancele Consultas sem criar conflitos de horário para o mesmo slot profissional, preservando histórico e sem antecipar o ciclo clínico posterior.

## Requirements

### Requirement: Administrador gerencia slots futuros de disponibilidade
O sistema MUST permitir que um Administrador autenticado crie slots de disponibilidade para profissionais ativos. Cada slot MUST pertencer a exatamente um profissional e a uma data/hora futura, e o par profissional + data/hora MUST ser único.

#### Scenario: Novo slot válido
- **WHEN** o Administrador seleciona um profissional ativo e informa uma data/hora futura ainda não registrada para esse profissional
- **THEN** o sistema cria exatamente um slot em estado disponível

#### Scenario: Slot duplicado
- **WHEN** o Administrador tenta criar outro slot para o mesmo profissional na mesma data/hora
- **THEN** o sistema rejeita a operação sem criar duplicidade

#### Scenario: Slot no passado
- **WHEN** o Administrador informa uma data/hora que não está no futuro segundo o timezone configurado da clínica
- **THEN** o servidor rejeita a criação

#### Scenario: Profissional inativo
- **WHEN** o Administrador tenta criar disponibilidade para um profissional inativo
- **THEN** o servidor rejeita a operação

### Requirement: Slot disponível pode ser desativado e reativado
O sistema MUST permitir que o Administrador desative um slot disponível e MUST permitir reativar um slot inativo que ainda esteja no futuro. Um slot reservado MUST NOT ser desativado diretamente.

#### Scenario: Desativar slot livre
- **WHEN** o Administrador desativa um slot futuro em estado disponível
- **THEN** o slot permanece persistido e passa a não aceitar novos agendamentos

#### Scenario: Reativar slot
- **WHEN** o Administrador reativa um slot inativo que permanece no futuro
- **THEN** o slot volta a aceitar agendamentos

#### Scenario: Tentar desativar slot reservado
- **WHEN** o Administrador tenta desativar um slot atualmente associado a uma Consulta não cancelada
- **THEN** o servidor rejeita a operação e preserva a reserva

### Requirement: Timezone da clínica é explícito
O sistema MUST interpretar datas/horários operacionais usando um timezone IANA explicitamente configurado para a clínica e MUST persistir os instantes de agenda de forma inequívoca.

#### Scenario: Configuração válida
- **WHEN** a aplicação recebe um timezone IANA válido na configuração da clínica
- **THEN** horários informados pela interface são interpretados nesse timezone e persistidos de forma consistente

#### Scenario: Configuração inválida ou ausente
- **WHEN** a aplicação precisa executar uma operação de agenda e o timezone da clínica não está configurado com um nome IANA válido
- **THEN** a operação é bloqueada com erro de configuração seguro em vez de assumir silenciosamente um fuso

### Requirement: Recepção consulta agenda por profissional e período
O sistema MUST permitir que a Recepcionista consulte slots e Consultas por profissional e intervalo de datas, apresentando horários disponíveis, reservados e inativos com estado textual.

#### Scenario: Agenda com horários mistos
- **WHEN** a Recepcionista consulta um período que contém slots disponíveis, reservados e inativos
- **THEN** a interface diferencia cada estado por texto e apresenta a Consulta associada quando houver reserva

#### Scenario: Período sem agenda
- **WHEN** não existem slots nem Consultas aplicáveis aos filtros
- **THEN** a interface apresenta um estado vazio compreensível sem criar dados fictícios

### Requirement: Recepção cria Consulta somente em slot disponível
O sistema MUST permitir que a Recepcionista agende uma Consulta relacionando um paciente existente a um slot futuro disponível de um profissional ativo. A nova Consulta MUST iniciar em estado `AGENDADA`.

#### Scenario: Agendamento válido
- **WHEN** a Recepcionista seleciona um paciente existente e um slot futuro disponível
- **THEN** o servidor cria exatamente uma Consulta `AGENDADA`, associa paciente, profissional, slot e data/hora e marca o slot como reservado na mesma transação

#### Scenario: Paciente inexistente
- **WHEN** a Recepcionista tenta agendar com uma identidade de paciente que não existe
- **THEN** o servidor rejeita a operação sem alterar o slot

#### Scenario: Slot indisponível
- **WHEN** a Recepcionista tenta agendar em slot inativo, reservado, passado ou inexistente
- **THEN** o servidor rejeita a operação e nenhuma Consulta é criada

#### Scenario: Profissional foi desativado
- **WHEN** o profissional do slot deixa de estar ativo antes da confirmação do agendamento
- **THEN** o servidor rejeita a nova Consulta e preserva o slot sem nova reserva

### Requirement: Reserva do slot é atômica
O sistema MUST garantir que um mesmo slot possua no máximo uma Consulta não cancelada, inclusive quando duas requisições tentarem reservar o mesmo horário simultaneamente.

#### Scenario: Duas recepcionistas reservam o mesmo slot
- **WHEN** duas requisições concorrentes tentam agendar pacientes no mesmo slot disponível
- **THEN** no máximo uma requisição cria uma Consulta ativa e a outra recebe conflito sem sobrescrever a reserva vencedora

#### Scenario: Constraint detecta inconsistência concorrente
- **WHEN** uma corrida ultrapassa validações de aplicação e atinge a persistência
- **THEN** a transação perdedora é revertida e o slot/Consulta permanecem consistentes

### Requirement: Recepção reagenda somente Consulta Agendada
O sistema MUST permitir que a Recepcionista reagende uma Consulta em estado `AGENDADA` para outro slot futuro disponível, preservando o paciente e substituindo profissional/data/hora conforme o novo slot.

#### Scenario: Reagendamento válido
- **WHEN** a Recepcionista move uma Consulta `AGENDADA` para outro slot disponível
- **THEN** o servidor libera o slot anterior, reserva o novo slot e atualiza profissional/data/hora da Consulta atomicamente

#### Scenario: Novo slot pertence a outro profissional
- **WHEN** o novo slot disponível pertence a outro profissional ativo
- **THEN** a Consulta mantém o mesmo paciente e passa a referenciar o novo profissional e horário

#### Scenario: Destino fica ocupado durante o reagendamento
- **WHEN** outra transação reserva o novo slot antes da conclusão do reagendamento
- **THEN** o reagendamento é rejeitado e a Consulta mantém integralmente o slot, profissional e horário anteriores

#### Scenario: Consulta não está Agendada
- **WHEN** a Recepcionista tenta reagendar uma Consulta em qualquer estado diferente de `AGENDADA`
- **THEN** o servidor rejeita a operação sem alterar a Consulta ou os slots envolvidos

### Requirement: Cancelamento preserva Consulta e devolve o slot
O sistema MUST permitir que a Recepcionista cancele uma Consulta em estado `AGENDADA` sem exclusão física. O cancelamento MUST alterar o estado para `CANCELADA`, registrar o momento e devolver o slot à disponibilidade quando ele ainda for futuro e ativo.

#### Scenario: Cancelamento válido
- **WHEN** a Recepcionista cancela uma Consulta `AGENDADA`
- **THEN** a Consulta permanece persistida como `CANCELADA` e o slot volta a ficar disponível quando elegível

#### Scenario: Consulta cancelada permanece no histórico da agenda
- **WHEN** a agenda do período é consultada após o cancelamento
- **THEN** a Consulta cancelada continua consultável com estado textual enquanto o slot pode ser novamente reservado

#### Scenario: Cancelamento repetido
- **WHEN** a Recepcionista tenta cancelar uma Consulta que já está `CANCELADA`
- **THEN** o servidor não executa uma nova transição nem altera timestamps previamente registrados

### Requirement: Estados clínicos posteriores não são manipulados por esta capability
O sistema MUST reconhecer os estados confirmados `AGENDADA`, `CONFIRMADA`, `EM_ANDAMENTO`, `CONCLUIDA` e `CANCELADA`, mas operações desta capability MUST criar somente `AGENDADA` e transicionar somente `AGENDADA → CANCELADA`.

#### Scenario: Estado posterior recebido em operação de agenda
- **WHEN** uma operação de reagendamento ou cancelamento recebe uma Consulta em `CONFIRMADA`, `EM_ANDAMENTO` ou `CONCLUIDA`
- **THEN** o servidor rejeita a mutação e preserva o registro para a futura capability de ciclo clínico

### Requirement: Agenda e disponibilidade são protegidas no servidor
O sistema MUST permitir gestão de slots somente à role Administrador e MUST permitir à Recepcionista operar agenda, agendamento, reagendamento e cancelamento conforme seu fluxo. O Paciente MUST poder consultar disponibilidade elegível e reservar exclusivamente para sua própria identidade autenticada, conforme patient-self-booking, sem autorização para operações da Recepção.

#### Scenario: Role incompatível tenta gerenciar disponibilidade
- **WHEN** uma identidade sem role Administrador chama diretamente uma mutação de slot
- **THEN** o servidor rejeita a operação antes de ler ou alterar dados protegidos

#### Scenario: Role incompatível tenta operar agendamento
- **WHEN** uma identidade sem role Recepcionista chama diretamente uma operação de agenda/Consulta desta capability
- **THEN** o servidor rejeita a operação e nenhum dado é retornado ou alterado indevidamente

### Requirement: Interfaces de agenda são acessíveis e responsivas
Os painéis Administrador e Recepção MUST oferecer estados de carregamento, vazio, erro, sucesso e conflito pertinentes; campos de data/hora e filtros MUST possuir labels associadas; estados de slot/Consulta MUST ser comunicados por texto e as ações essenciais MUST funcionar por teclado e em telas estreitas.

#### Scenario: Erro de conflito
- **WHEN** uma reserva ou reagendamento perde uma disputa concorrente por um slot
- **THEN** a interface apresenta feedback compreensível e preserva a seleção necessária para que a Recepção escolha outro horário

#### Scenario: Operação em tela estreita
- **WHEN** Administrador ou Recepcionista utiliza a agenda em viewport estreita
- **THEN** filtros, slots e ações permanecem legíveis e operáveis sem exigir rolagem horizontal para a tarefa principal

### Requirement: Horários são apresentados por dia em linguagem operacional
O sistema MUST mostrar horários reais agrupados por data local da clínica, identificando hora, profissional e situação textual. A interface de Administração e Recepção MUST evitar termos técnicos como "slot" para orientar o usuário.

#### Scenario: Dias e profissionais diferentes
- **WHEN** há horários futuros em vários dias e profissionais
- **THEN** a interface os agrupa por data, mantendo hora e profissional em cada item e ordenação temporal

#### Scenario: Sem horários no filtro
- **WHEN** o período escolhido não contém horários disponíveis
- **THEN** o sistema apresenta orientação simples para alterar período ou profissional, sem criar dados fictícios

### Requirement: Cadastro de horário usa data e hora separadas
O Administrador MUST informar profissional, data e hora em campos independentes, com labels e validação acessível; o backend MUST manter o mesmo contrato de horário local e unicidade do domínio.

#### Scenario: Horário válido
- **WHEN** o Administrador escolhe profissional ativo, data futura e hora
- **THEN** a aplicação combina os valores no horário local da clínica e persiste a disponibilidade usando o serviço autorizado existente

#### Scenario: Data ou hora ausente
- **WHEN** o Administrador tenta salvar sem data ou sem hora
- **THEN** recebe erro legível e nenhum horário parcial é persistido

#### Scenario: Horário duplicado
- **WHEN** o Administrador escolhe profissional e data/hora já cadastrados
- **THEN** o serviço existente rejeita o conflito sem criar duplicidade

### Requirement: Recepção agenda consulta no modal compartilhado
A Recepção MUST disponibilizar um diálogo único para agendamento a partir da Agenda ou do dashboard. O diálogo MUST permitir escolher um paciente existente autorizado, médico ativo, data e horário reservável, revisar os dados e confirmar utilizando o serviço transacional já existente, sem criar uma rota obrigatória nem uma reserva paralela.

#### Scenario: Agendamento concluído pela Agenda
- **WHEN** a recepcionista abre o modal, seleciona paciente, médico, dia com slot disponível e horário e confirma a revisão
- **THEN** o servidor revalida a reserva, persiste exatamente uma Consulta e a interface fecha o modal, informa sucesso e atualiza a consulta no período correspondente sem realizar check-in

#### Scenario: Agendamento iniciado no dashboard
- **WHEN** a recepcionista aciona Nova consulta no dashboard
- **THEN** o mesmo modal é aberto no dashboard, sem navegação obrigatória para outro formulário

#### Scenario: Profissional sem especialidade vinculada
- **WHEN** o cadastro de um médico ativo não possui especialidade ativa vinculada
- **THEN** a seleção do profissional continua possível sem inventar nem exigir especialidade

#### Scenario: Horário reservado por outra sessão
- **WHEN** o horário é reservado por outra sessão depois de exibido no modal
- **THEN** o servidor rejeita a reserva concorrente sem criar duplicidade e a interface recarrega a disponibilidade, preservando paciente e profissional

#### Scenario: Nenhum horário disponível
- **WHEN** não existem slots futuros disponíveis no intervalo de 45 dias para o profissional
- **THEN** o calendário não oferece dias reserváveis e a interface mostra orientação contextual sem criar horário fictício

#### Scenario: Descarte antes de confirmar
- **WHEN** uma recepcionista fecha o modal com seleção ou busca preenchida
- **THEN** a interface confirma a intenção de descartar, permitindo continuar com os dados existentes

#### Scenario: Consulta salva e falha no refresh
- **WHEN** a persistência confirma a consulta mas a leitura para atualizar Agenda ou dashboard falha
- **THEN** a interface informa que a reserva foi salva e pede atualização, sem sugerir nova confirmação

### Requirement: Recepção utiliza identidade mínima na busca de agendamento
A pesquisa de paciente MUST consultar identidades autorizadas por nome, CPF ou telefone e apresentar somente nome e identificação de contato mascarada. O sistema MUST revalidar o paciente selecionado no servidor antes de confirmar.

#### Scenario: Buscar paciente existente
- **WHEN** a recepcionista digita pelo menos dois caracteres de nome, CPF ou telefone e busca
- **THEN** aparecem somente resultados reais com telefone parcial e nenhum CPF exposto

#### Scenario: Paciente não encontrado
- **WHEN** a pesquisa não encontra pacientes
- **THEN** o diálogo informa ausência de resultados e oferece a rota de cadastro existente, sem duplicar o formulário

### Requirement: Agenda da Recepção apresenta um único período autorizado
O sistema MUST consultar consultas persistidas por Recepcionista autorizada e MUST usar o mesmo recorte de profissional e sete dias locais para calendário e listagem. MUST NOT preencher dias com horários fictícios nem devolver dados para perfil não autorizado.

#### Scenario: Filtro combinado
- **WHEN** a Recepcionista aplica profissional e data inicial
- **THEN** as duas visualizações exibem somente consultas daquele profissional nas mesmas sete datas

#### Scenario: Sem consultas
- **WHEN** o período não contém consultas
- **THEN** os dias exibem contagem zero e a lista apresenta estado vazio não técnico

#### Scenario: Acesso negado
- **WHEN** uma sessão sem role Recepcionista consulta a agenda
- **THEN** o servidor nega a leitura antes de retornar dados pessoais

### Requirement: Navegação semanal e seleção de dia
A agenda MUST navegar de sete em sete dias, voltar à data atual da clínica e aceitar início de período válido. MUST permitir selecionar e remover o filtro por dia, preservar ordenação cronológica e indicar consultas além da prévia.

#### Scenario: Próxima semana
- **WHEN** a Recepcionista avança sete dias
- **THEN** data inicial e final são recalculadas, a seleção anterior é removida e o profissional é preservado

#### Scenario: Filtrar e desfiltrar data
- **WHEN** um dia é selecionado e selecionado novamente
- **THEN** a lista primeiro mostra somente aquela data e depois retorna ao período inteiro

#### Scenario: Data inválida
- **WHEN** a data digitada é inválida
- **THEN** é exibido erro e não é solicitada consulta para um intervalo incorreto

#### Scenario: Muitas consultas
- **WHEN** um dia contém mais de duas consultas
- **THEN** a grade mostra duas prévias, o número restante e acesso à lista paginada

### Requirement: Ações de consulta preservam os fluxos existentes
A agenda MUST manter um único acesso à página dedicada de agendamento. Check-in, reagendamento e cancelamento MUST utilizar handlers existentes que revalidam role, recurso, estado e integridade no servidor. Estados MUST ter rótulo textual e ações acessíveis em mobile e por teclado.

#### Scenario: Chegada válida
- **WHEN** a Recepcionista confirma chegada de consulta elegível
- **THEN** a transição é persistida pelo serviço existente e agenda/fila são atualizadas

#### Scenario: Chegada duplicada
- **WHEN** uma consulta já confirmada recebe nova tentativa de check-in
- **THEN** o servidor rejeita a transição sem criar entrada duplicada

#### Scenario: Nova reserva
- **WHEN** uma consulta é criada no fluxo dedicado
- **THEN** o sistema retorna à agenda no período do agendamento recém-criado

#### Scenario: Mobile
- **WHEN** a agenda é exibida a 320 px
- **THEN** o calendário e cartões não provocam overflow horizontal da página e mantêm as ações autorizadas

### Requirement: Administração consulta a disponibilidade por profissional e dia
A interface administrativa MUST manter um único médico selecionado ao alternar entre consulta da agenda, expediente semanal e inclusão de horário avulso. A consulta mensal MUST exibir somente os slots persistidos do médico e do mês escolhidos, permitindo inspecionar dias sem horários.

#### Scenario: Alterar médico
- **WHEN** o Administrador seleciona outro médico ativo
- **THEN** o servidor revalida acesso e a interface carrega os horários e a regra semanal do médico escolhido sem misturar dados do profissional anterior

#### Scenario: Consultar dia sem horários
- **WHEN** o Administrador seleciona um dia do mês visível que não possui slots persistidos
- **THEN** a interface mostra esse dia como selecionado e informa que não há horários cadastrados, sem criar disponibilidade artificial

#### Scenario: Consultar dia com disponibilidade
- **WHEN** o Administrador seleciona um dia com slots persistidos
- **THEN** a interface apresenta apenas os horários desse dia em ordem cronológica, com contagens de disponível, reservado e inativo derivadas dos registros autorizados

### Requirement: Administração confirma desativação sem afetar reservas
A interface administrativa MUST solicitar confirmação contextual antes de desativar um horário disponível e MUST NOT disponibilizar desativação direta para slot reservado. O serviço MUST validar novamente status e autorização, inclusive quando o estado se altera entre a leitura e a confirmação.

#### Scenario: Desativação válida
- **WHEN** o Administrador confirma a desativação de um slot ainda disponível
- **THEN** a operação persiste o novo estado e atualiza o calendário, sem alterar nenhuma Consulta

#### Scenario: Slot reservado antes de confirmar
- **WHEN** um horário é reservado por outra transação antes da confirmação da desativação
- **THEN** a mutação administrativa é rejeitada e a Consulta permanece preservada

### Requirement: Expediente atual é distinguível de edição pendente
A interface MUST indicar a regra semanal persistida do médico sem confundi-la com campos ainda não salvos. O formulário MUST explicar o intervalo contínuo de dias suportado pelo modelo vigente.

#### Scenario: Editar sem salvar
- **WHEN** o Administrador modifica os campos da regra semanal sem submetê-los
- **THEN** o resumo do expediente salvo permanece representando somente a regra persistida

### Requirement: Agenda administrativa em modo QA somente leitura
O sistema MUST disponibilizar ao Administrador autenticado a visualização da agenda em `/admin/agenda` somente quando o modo de QA local estiver explicitamente habilitado. Cada consulta MUST revalidar sessão, role e flag no servidor, sem permitir mutações de consulta ou slot.

#### Scenario: Preview disponível
- **WHEN** o Administrador autenticado abre a agenda com a flag QA habilitada
- **THEN** o sistema exibe a data atual no fuso da clínica e permite consultar médicos e meses a partir de dados persistidos.

#### Scenario: Acesso não autorizado
- **WHEN** o modo QA está desabilitado, a sessão expirou ou a role não é Administrador
- **THEN** nenhuma informação de agenda é retornada e o acesso é bloqueado ou redirecionado conforme a política de autenticação.

### Requirement: Agenda contextual por médico e dia
O sistema MUST filtrar slots e consultas persistidos em conjunto por profissional e mês, mostrar os dias com registros no calendário e detalhar o dia selecionado em ordem cronológica, com paginação em listas extensas.

#### Scenario: Sem registros na data
- **WHEN** a data selecionada não possui horários ou consultas autorizadas
- **THEN** o sistema exibe estados vazios compactos, sem produzir horários fictícios.

#### Scenario: Combinação de filtros
- **WHEN** o Administrador muda médico, mês ou dia
- **THEN** a interface limpa resultados anteriores durante o carregamento e mostra contagens derivadas apenas dos registros que correspondem aos filtros.

### Requirement: Projeção administrativa mínima de consulta
A visualização QA MUST exibir somente horário, médico e estado persistido das consultas; não MUST transmitir nome, CPF, sintomas, diagnóstico, prescrição ou demais campos clínicos do paciente.

#### Scenario: Consulta associada a paciente
- **WHEN** uma consulta persistida é incluída no preview
- **THEN** a projeção contém apenas os campos administrativos mínimos e não concede ao Administrador acesso ao fluxo de edição da Recepção.

### Requirement: Agendamento compartilhado a partir da ficha
A Recepção SHALL reutilizar o mesmo formulário, State e serviço transacional de agendamento a partir do dashboard, da Agenda e da Ficha, em um modal acessível. O fluxo SHALL validar sessão, paciente e slot no servidor, impedir conflitos e atualizar o contexto após reserva bem-sucedida.

#### Scenario: Agendar a partir da ficha
- **WHEN** a recepcionista abre o modal pela ficha de um paciente autorizado
- **THEN** o paciente da ficha aparece selecionado e não pode ser substituído no modal
- **AND** os horários disponíveis vêm da Agenda persistida
- **AND** a recepcionista revisa paciente, profissional, data e horário antes de confirmar
- **WHEN** a recepcionista confirma uma reserva disponível
- **THEN** a consulta é persistida pelo serviço de agendamento existente
- **AND** o modal fecha e as próximas consultas da ficha são atualizadas

#### Scenario: Reserva conflitante ou repetida
- **WHEN** uma reserva é solicitada para um horário indisponível ou já reservado
- **THEN** o serviço recusa a reserva sem duplicar registros
- **AND** o modal permanece disponível para correção, com feedback de erro

#### Scenario: Agendar pela Agenda ou dashboard
- **WHEN** a recepcionista inicia uma nova consulta pela Agenda ou dashboard
- **THEN** o mesmo modal exige seleção de paciente e horário
- **AND** a rota de agendamento preexistente permanece compatível

### Requirement: Expediente semanal gera horários sem sobrescrever reservas
O sistema MUST persistir expediente semanal por profissional ativo, validar dias e horários elegíveis e publicar slots dentro da janela móvel de 45 dias em horário local da clínica, sem sobrescrever reservas nem indisponibilidades manuais.

#### Scenario: Regra semanal válida
- **WHEN** o Administrador salva uma faixa contínua de dias e intervalo com duração de slot suportada (30 ou 60 minutos)
- **THEN** o serviço gera os horários elegíveis na janela móvel, convertendo instantes conforme o fuso configurado

#### Scenario: Regeração de slots
- **WHEN** o processo de publicação é repetido para profissional com slots existentes
- **THEN** as reservas e os horários manuais desativados permanecem intactos, sem criar duplicações

#### Scenario: Regra inválida
- **WHEN** dias, início, fim ou duração não respeitam as regras do expediente
- **THEN** o serviço rejeita a alteração e preserva a regra persistida

### Requirement: Exportação de Consulta para iCalendar respeita identidade e privacidade
O sistema MUST permitir exportar arquivo .ics de Consulta autorizada e não cancelada com instante inicial verdadeiro, sem inventar duração, local ou dados clínicos.

#### Scenario: Consulta autorizada
- **WHEN** usuário autorizado solicita o evento de uma consulta ativa com horário válido
- **THEN** o serviço produz iCalendar importável contendo apenas informações operacionais necessárias e data/hora com fuso correto

#### Scenario: Consulta cancelada ou não autorizada
- **WHEN** a consulta está cancelada, pertence a outro paciente/médico ou não existe sessão elegível
- **THEN** o servidor rejeita a exportação sem revelar dados

#### Scenario: Dados insuficientes
- **WHEN** a consulta possui horário sem fuso válido
- **THEN** a geração é rejeitada em vez de fabricar horário ou duração
