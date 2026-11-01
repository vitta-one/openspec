## ADDED Requirements

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
