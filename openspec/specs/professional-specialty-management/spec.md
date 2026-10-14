# professional-specialty-management Specification

## Purpose

Permitir que o Administrador mantenha o diretório de profissionais e especialidades da clínica, incluindo associações entre eles e vínculo opcional com uma identidade médica local, sem antecipar regras de agenda ou Consulta.

## Requirements

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
O sistema MUST permitir cadastrar profissional com nome, e-mail único e ao menos uma especialidade ativa sem pedir identificador interno nem vínculo manual de conta. MUST gerar identificador interno único, sem simular CRM, e vincular exatamente uma identidade `MEDICO` válida. Edição legada MUST preservar vínculos existentes.

#### Scenario: Novo profissional válido
- **WHEN** o Administrador informa nome, e-mail profissional válido e ao menos uma especialidade ativa
- **THEN** o sistema cria exatamente um profissional ativo, associações e identidade Médica vinculada sem exigir preenchimento do identificador interno

#### Scenario: Identificador profissional duplicado
- **WHEN** a operação legada de domínio tenta cadastrar ou editar um profissional com identificador interno já atribuído
- **THEN** o servidor rejeita a duplicidade sem alterar registros existentes; o fluxo simplificado gera identificador interno único

#### Scenario: Profissional sem especialidade
- **WHEN** o Administrador tenta salvar um profissional sem especialidades
- **THEN** o servidor rejeita a operação sem criar identidade órfã ou profissional parcial

#### Scenario: Cadastro médico novo
- **WHEN** o Administrador salva nome, e-mail e especialidades válidas
- **THEN** o sistema persiste profissional, conta MEDICO e associações atomicamente, gerando identificador interno e credencial temporária segura

#### Scenario: E-mail já cadastrado
- **WHEN** o e-mail normalizado pertence a conta de outra role ou Médico já vinculado
- **THEN** o servidor rejeita o cadastro sem alterar registros ou senhas existentes

#### Scenario: Conta Médica disponível
- **WHEN** o e-mail pertence a conta MEDICO sem vínculo
- **THEN** o servidor reutiliza essa identidade sem redefinir a senha e cria associação única

#### Scenario: Falha na associação
- **WHEN** associação ou constraint falha após iniciar o cadastro
- **THEN** nenhuma identidade órfã ou profissional parcial é persistido

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
O painel administrativo MUST apresentar estados de carregamento, vazio, erro e sucesso relevantes; MUST manter listas de especialidades e profissionais como conteúdo principal; e MUST abrir formulários de criação/edição em diálogos modais acessíveis sem remover o contexto do diretório.

#### Scenario: Nenhum profissional cadastrado
- **WHEN** o Administrador acessa o diretório e não existe profissional cadastrado
- **THEN** a interface apresenta estado vazio compreensível e a ação de cadastrar o primeiro profissional abre o formulário correspondente em diálogo

#### Scenario: Nenhuma especialidade cadastrada
- **WHEN** o Administrador acessa a gestão de especialidades e não existe especialidade cadastrada
- **THEN** a interface apresenta estado vazio compreensível e a ação de cadastrar a primeira especialidade abre o formulário correspondente em diálogo

#### Scenario: Abrir criação de especialidade
- **WHEN** o Administrador aciona “Nova especialidade”
- **THEN** a interface abre um diálogo nomeado com o campo e ações necessárias sem substituir a lista do diretório

#### Scenario: Abrir criação de profissional
- **WHEN** o Administrador aciona “Novo profissional”
- **THEN** a interface abre um diálogo nomeado contendo o formulário completo, preservando o diretório em segundo plano

#### Scenario: Validação falha dentro do diálogo
- **WHEN** o servidor rejeita criação ou edição por validação ou conflito
- **THEN** o diálogo permanece aberto, o feedback é apresentado e os valores corrigíveis permanecem disponíveis

#### Scenario: Operação concluída
- **WHEN** criação ou edição é persistida com sucesso
- **THEN** o diálogo é fechado, a lista é atualizada e o sucesso é comunicado na região de feedback do diretório

#### Scenario: Cancelamento
- **WHEN** o Administrador cancela ou fecha o diálogo sem salvar
- **THEN** o formulário transitório é limpo e nenhum registro é alterado

#### Scenario: Erro server-side
- **WHEN** uma operação administrativa falha
- **THEN** a interface apresenta feedback acessível sem expor stack trace, credenciais ou outros dados sensíveis

### Requirement: Painel administrativo exibe um resumo recente do diretório
O sistema MUST limitar o painel inicial às três especialidades e aos três profissionais mais recentemente criados, ordenados por data de criação decrescente e ID decrescente em empate, com dados reais e identidade de situação.

#### Scenario: Há mais de três especialidades
- **WHEN** o Administrador abre o painel com cinco especialidades persistidas
- **THEN** a superfície inicial apresenta apenas as três mais recentes e o link "Ver todas" abre a tela completa

#### Scenario: Há mais de três profissionais
- **WHEN** o Administrador abre o painel com cinco profissionais persistidos
- **THEN** o painel apresenta apenas os três mais recentes e o link "Ver todos" abre a tela completa

#### Scenario: Nenhum registro
- **WHEN** ainda não existem especialidades ou profissionais
- **THEN** o respectivo card mostra uma orientação clara com ação de cadastro

### Requirement: Especialidades e profissionais possuem páginas completas de gestão
O sistema MUST oferecer páginas administrativas distintas para listagem, pesquisa, filtro de situação, paginação e operações de edição e ativação existentes.

#### Scenario: Pesquisa sem resultado
- **WHEN** a pesquisa não encontra registros
- **THEN** a página apresenta estado vazio apropriado, sem apagar ou modificar dados

#### Scenario: Navegação e paginação
- **WHEN** o Administrador abre uma página completa e avança entre páginas
- **THEN** os controles informam estado atual e evitam navegação fora dos limites

### Requirement: Interações administrativas são acessíveis
Links e botões habilitados MUST oferecer feedback visual de interação, foco visível, tamanho adequado e ações por teclado, sem atribuir falsa interatividade a containers estáticos.

#### Scenario: Navegar sem mouse
- **WHEN** o Administrador usa Tab e Enter para acessar "Ver todas"
- **THEN** o foco está visível e a rota de destino abre corretamente

### Requirement: E-mail de onboarding reflete status real
O sistema MUST registrar se um e-mail de boas-vindas foi aceito pelo serviço externo, não enviado, falhou ou está indeterminado. MUST impedir que ausência de credenciais Resend seja apresentada como envio concluído.

#### Scenario: Resend não configurado
- **WHEN** não há configuração válida do Resend no servidor
- **THEN** o cadastro local pode concluir, mas o sistema informa que o e-mail não foi enviado

#### Scenario: Provedor confirma aceitação
- **WHEN** a API Resend aceita a requisição de boas-vindas
- **THEN** o estado registrado indica aceitação pelo provedor, sem afirmar entrega ou leitura

#### Scenario: Erro ou timeout
- **WHEN** o provedor falha ou não fornece confirmação conclusiva
- **THEN** o servidor não expõe segredo e sinaliza falha ou estado indeterminado, sem reenvio cego
