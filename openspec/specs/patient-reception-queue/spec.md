# patient-reception-queue Specification

## Purpose

Permitir que a Recepção registre pacientes e mantenha uma fila operacional priorizada, enquanto Médicos chamam e finalizam o próximo atendimento sem que o sistema execute triagem clínica ou altere automaticamente a gravidade informada.

## Requirements

### Requirement: Cadastro mínimo de paciente pela Recepção
O sistema MUST permitir que um usuário com role Recepcionista cadastre um paciente com nome e CPF válidos. O CPF MUST ser normalizado para persistência e MUST permanecer único.

#### Scenario: Novo paciente válido
- **WHEN** uma Recepcionista autenticada informa nome e CPF válidos ainda não cadastrados
- **THEN** o sistema cria exatamente um paciente e disponibiliza esse paciente para entrada na fila

#### Scenario: CPF inválido
- **WHEN** a Recepcionista informa um CPF que não possui formato e dígitos verificadores válidos
- **THEN** o sistema rejeita o cadastro sem persistir o paciente e apresenta erro associado ao campo

#### Scenario: CPF já cadastrado
- **WHEN** a Recepcionista tenta cadastrar um CPF já existente
- **THEN** o sistema não cria paciente duplicado e informa que o cadastro existente deve ser utilizado

### Requirement: Entrada na fila usa prioridade informada pela operação
O sistema MUST permitir que a Recepcionista crie uma entrada de fila para um paciente cadastrado informando sintomas, prioridade e o momento de entrada. A prioridade MUST aceitar somente `VERMELHO`, `AMARELO` ou `VERDE`. O sistema MUST NOT inferir, calcular ou recomendar prioridade clínica.

#### Scenario: Paciente entra na fila
- **WHEN** a Recepcionista seleciona um paciente, registra sintomas e uma prioridade válida
- **THEN** o sistema cria uma entrada com estado `AGUARDANDO` e registra o horário de entrada no servidor

#### Scenario: Prioridade ausente ou inválida
- **WHEN** a entrada é submetida sem uma das três prioridades permitidas
- **THEN** o servidor rejeita a operação e nenhuma entrada de fila é criada

### Requirement: Ordenação determinística da fila
O sistema MUST ordenar entradas em estado `AGUARDANDO` por prioridade `VERMELHO` antes de `AMARELO` antes de `VERDE`; entradas da mesma prioridade MUST ser ordenadas pelo horário de entrada mais antigo e, em último empate, pelo identificador persistido.

#### Scenario: Prioridades diferentes
- **WHEN** existem pacientes aguardando com prioridades diferentes
- **THEN** todos os pacientes vermelhos aparecem antes dos amarelos e todos os amarelos antes dos verdes

#### Scenario: Mesma prioridade
- **WHEN** duas entradas aguardando possuem a mesma prioridade
- **THEN** a entrada mais antiga aparece primeiro

### Requirement: Tempo de espera não altera automaticamente a prioridade
O sistema MUST NOT elevar ou reduzir automaticamente a prioridade de uma entrada com base no tempo decorrido.

#### Scenario: Paciente permanece aguardando
- **WHEN** uma entrada permanece na fila por qualquer duração sem reavaliação manual
- **THEN** a prioridade armazenada permanece inalterada

### Requirement: Reavaliação manual enquanto aguarda
O sistema MUST permitir que a Recepcionista altere sintomas e prioridade somente enquanto a entrada estiver em estado `AGUARDANDO`. Após a atualização, a posição exibida MUST refletir novamente as regras de ordenação.

#### Scenario: Reavaliação aumenta prioridade
- **WHEN** uma Recepcionista altera uma entrada aguardando de `VERDE` para `VERMELHO`
- **THEN** o sistema persiste a nova prioridade e reposiciona a entrada segundo a ordenação da fila

#### Scenario: Reavaliação de entrada já chamada
- **WHEN** a Recepcionista tenta alterar sintomas ou prioridade de uma entrada que não está mais `AGUARDANDO`
- **THEN** o servidor rejeita a alteração e preserva os dados existentes

### Requirement: Retirada da fila preserva histórico
O sistema MUST permitir que a Recepcionista retire uma entrada em espera informando um motivo operacional, sem excluir fisicamente o registro.

#### Scenario: Desistência ou não comparecimento
- **WHEN** a Recepcionista retira uma entrada aguardando e informa o motivo
- **THEN** o sistema altera o estado para `RETIRADO`, registra momento e motivo da retirada e remove a entrada da fila ativa

#### Scenario: Tentativa de retirar atendimento em andamento
- **WHEN** a Recepcionista tenta retirar uma entrada que já está em atendimento ou finalizada
- **THEN** o servidor rejeita a transição

### Requirement: Médico chama atomicamente o próximo paciente
O sistema MUST permitir que um usuário com role Médico chame o próximo paciente elegível da fila. A seleção e a alteração de estado MUST ocorrer de forma atômica para que a mesma entrada não seja atribuída simultaneamente a dois Médicos.

#### Scenario: Médico chama próximo
- **WHEN** um Médico autenticado solicita o próximo paciente e existe pelo menos uma entrada aguardando
- **THEN** o servidor seleciona a primeira entrada pela ordenação, altera seu estado para `EM_ATENDIMENTO`, associa o Médico autenticado e registra o momento da chamada

#### Scenario: Dois Médicos chamam simultaneamente
- **WHEN** dois Médicos solicitam o próximo paciente de forma concorrente
- **THEN** cada entrada pode ser atribuída a no máximo um Médico e nenhum paciente é chamado duas vezes

#### Scenario: Fila vazia
- **WHEN** um Médico solicita o próximo paciente e não existe entrada aguardando
- **THEN** o sistema não cria nem altera registros e apresenta um estado de fila vazia

### Requirement: Médico finaliza somente seu atendimento ativo
O sistema MUST permitir que o Médico finalize uma entrada em `EM_ATENDIMENTO` somente quando ela estiver associada à sua própria identidade autenticada.

#### Scenario: Finalização válida
- **WHEN** o Médico responsável finaliza seu atendimento ativo
- **THEN** o sistema altera a entrada para `FINALIZADO` e registra o momento da finalização

#### Scenario: Médico diferente tenta finalizar
- **WHEN** outro Médico tenta finalizar diretamente uma entrada que não lhe pertence
- **THEN** o servidor rejeita a operação e não altera a entrada

### Requirement: Acesso à fila é protegido no servidor
O sistema MUST permitir operações de cadastro, reavaliação e retirada somente à role Recepcionista e MUST permitir chamada/finalização somente à role Médico. Dados de sintomas MUST NOT ser expostos em rotas públicas.

#### Scenario: Role incompatível aciona operação
- **WHEN** uma identidade autenticada sem a role exigida chama diretamente um handler da fila
- **THEN** o servidor rejeita a operação antes de ler ou modificar dados protegidos

### Requirement: Interfaces operacionais acessíveis e responsivas
Os painéis de Recepção e Médico MUST oferecer estados de carregamento, vazio, erro e sucesso pertinentes; formulários MUST possuir labels, mensagens de erro associadas e foco visível; as ações essenciais MUST ser utilizáveis por teclado e em telas estreitas.

#### Scenario: Fila sem pacientes
- **WHEN** a Recepção ou o Médico acessa seu painel e não há entradas aplicáveis
- **THEN** a interface apresenta um estado vazio compreensível sem simular dados

#### Scenario: Erro de operação
- **WHEN** uma operação server-side da fila falha
- **THEN** a interface apresenta feedback acessível sem expor detalhes internos ou dados sensíveis
