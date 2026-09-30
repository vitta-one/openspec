## Purpose

Permitir que o Administrador mantenha o diretório de profissionais e especialidades da clínica, incluindo associações entre eles e vínculo opcional com uma identidade médica local, sem antecipar regras de agenda ou Consulta.

## ADDED Requirements

### Requirement: Administrador gerencia especialidades
O sistema MUST permitir que um usuário com role Administrador cadastre, consulte e edite especialidades da clínica. Cada especialidade MUST possuir um nome não vazio e único segundo uma comparação normalizada que desconsidere espaços periféricos e diferenças de caixa.

#### Scenario: Nova especialidade válida
- **WHEN** um Administrador autenticado informa um nome válido ainda não cadastrado
- **THEN** o sistema cria uma especialidade ativa e a disponibiliza para associação a profissionais

#### Scenario: Especialidade duplicada
- **WHEN** o Administrador tenta cadastrar ou renomear uma especialidade para um nome equivalente a outro já existente após normalização
- **THEN** o sistema rejeita a operação sem criar duplicidade

#### Scenario: Nome inválido
- **WHEN** o Administrador informa um nome vazio ou acima do limite permitido
- **THEN** o servidor rejeita a operação e nenhuma alteração é persistida

### Requirement: Especialidade é desativada sem exclusão física
O sistema MUST permitir que o Administrador altere uma especialidade entre ativa e inativa sem excluir fisicamente seu registro.

#### Scenario: Desativação
- **WHEN** o Administrador desativa uma especialidade ativa
- **THEN** o registro permanece persistido, passa a ser identificado como inativo e deixa de poder ser selecionado em novas associações

#### Scenario: Reativação
- **WHEN** o Administrador reativa uma especialidade inativa
- **THEN** a especialidade volta a poder ser selecionada em novas associações

### Requirement: Administrador gerencia profissionais
O sistema MUST permitir que um Administrador cadastre, consulte e edite profissionais com nome, identificador profissional único e estado ativo/inativo.

#### Scenario: Novo profissional válido
- **WHEN** o Administrador informa nome, identificador profissional válido e ao menos uma especialidade ativa
- **THEN** o sistema cria exatamente um profissional ativo com suas associações de especialidade

#### Scenario: Identificador profissional duplicado
- **WHEN** o Administrador tenta cadastrar ou editar um profissional usando identificador profissional já atribuído a outro profissional
- **THEN** o servidor rejeita a operação sem alterar o registro existente

#### Scenario: Profissional sem especialidade
- **WHEN** o Administrador tenta salvar um profissional sem nenhuma especialidade associada
- **THEN** o servidor rejeita a operação

### Requirement: Relação entre profissionais e especialidades é muitos-para-muitos
O sistema MUST permitir que um profissional esteja associado a uma ou mais especialidades e MUST permitir que uma especialidade esteja associada a vários profissionais.

#### Scenario: Profissional com múltiplas especialidades
- **WHEN** o Administrador seleciona duas ou mais especialidades ativas para um profissional
- **THEN** todas as associações são persistidas sem duplicidade

#### Scenario: Especialidade compartilhada
- **WHEN** dois profissionais diferentes são associados à mesma especialidade ativa
- **THEN** ambas as associações são aceitas e permanecem independentes

#### Scenario: Associação duplicada
- **WHEN** a mesma especialidade é enviada mais de uma vez para o mesmo profissional
- **THEN** o sistema mantém no máximo uma associação persistida para esse par

### Requirement: Especialidade inativa não pode entrar em nova associação
O sistema MUST impedir que uma especialidade inativa seja adicionada ou utilizada para substituir as especialidades de um profissional.

#### Scenario: Tentativa de associação inativa
- **WHEN** o Administrador tenta salvar um profissional incluindo uma especialidade inativa
- **THEN** o servidor rejeita a operação e preserva as associações anteriores

#### Scenario: Associação histórica após desativação
- **WHEN** uma especialidade já associada a um profissional é desativada posteriormente
- **THEN** a associação existente permanece preservada para rastreabilidade, mas a especialidade é identificada como inativa

### Requirement: Profissional pode possuir vínculo opcional com uma conta Médica
O sistema MUST permitir que um profissional possua zero ou uma conta local associada e MUST aceitar somente contas com role `MEDICO`. Uma mesma conta `MEDICO` MUST estar associada a no máximo um profissional.

#### Scenario: Vínculo válido com Médico
- **WHEN** o Administrador associa a um profissional uma conta existente com role `MEDICO` ainda não vinculada a outro profissional
- **THEN** o sistema persiste o vínculo

#### Scenario: Profissional sem conta
- **WHEN** o Administrador salva um profissional sem selecionar uma conta
- **THEN** o profissional permanece válido e pode existir sem credencial de acesso

#### Scenario: Role incompatível
- **WHEN** o Administrador tenta vincular uma conta Administrador, Recepcionista ou Financeiro
- **THEN** o servidor rejeita o vínculo

#### Scenario: Conta Médica já vinculada
- **WHEN** o Administrador tenta associar a mesma conta `MEDICO` a um segundo profissional
- **THEN** o servidor rejeita a operação e mantém o vínculo original

### Requirement: Profissional é desativado sem exclusão física
O sistema MUST permitir que o Administrador altere um profissional entre ativo e inativo sem apagar seu registro, identificador, especialidades ou vínculo de conta.

#### Scenario: Desativação de profissional
- **WHEN** o Administrador desativa um profissional ativo
- **THEN** o profissional permanece persistido, é exibido como inativo e deixa de ser elegível para novos fluxos que exijam profissional ativo

#### Scenario: Reativação de profissional
- **WHEN** o Administrador reativa um profissional inativo
- **THEN** o profissional volta a ser elegível para fluxos futuros que exijam profissional ativo, desde que suas demais validações permaneçam satisfeitas

### Requirement: Somente Administrador acessa operações de gestão
O sistema MUST revalidar no servidor a sessão e a role `ADMINISTRADOR` em toda leitura ou mutação de profissionais, especialidades e vínculos desta capability.

#### Scenario: Role incompatível solicita lista
- **WHEN** uma identidade autenticada com role Recepcionista, Médico ou Financeiro tenta chamar diretamente uma operação de consulta desta capability
- **THEN** o servidor rejeita a operação sem retornar o diretório protegido

#### Scenario: Role incompatível tenta mutação
- **WHEN** uma identidade autenticada sem role Administrador tenta criar, editar, ativar, desativar ou alterar associações
- **THEN** o servidor rejeita a operação e nenhum dado é alterado

### Requirement: Diretório administrativo oferece estados operacionais acessíveis
O painel administrativo MUST apresentar estados de carregamento, vazio, erro e sucesso relevantes; formulários MUST possuir labels e mensagens associadas; ações essenciais MUST ser utilizáveis por teclado e em telas estreitas.

#### Scenario: Nenhum profissional cadastrado
- **WHEN** o Administrador acessa o diretório e não existe profissional cadastrado
- **THEN** a interface apresenta estado vazio compreensível e a ação de cadastrar o primeiro profissional

#### Scenario: Nenhuma especialidade cadastrada
- **WHEN** o Administrador acessa a gestão de especialidades e não existe especialidade cadastrada
- **THEN** a interface apresenta estado vazio compreensível e a ação de cadastrar a primeira especialidade

#### Scenario: Erro server-side
- **WHEN** uma operação administrativa falha
- **THEN** a interface apresenta feedback acessível sem expor stack trace, credenciais ou outros dados sensíveis
