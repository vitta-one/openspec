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
O sistema MUST permitir gestão de slots somente à role Administrador e MUST permitir consulta operacional da agenda, agendamento, reagendamento e cancelamento somente à role Recepcionista.

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
