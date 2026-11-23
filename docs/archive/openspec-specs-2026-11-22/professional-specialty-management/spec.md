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
O sistema MUST permitir que o Administrador altere uma especialidade entre ativa e inativa sem excluir fisicamente seu registro. A interface de gestão MUST exigir confirmação contextual antes de persistir uma alteração de situação, exibindo nome e situação atuais. Cancelar o diálogo MUST preservar integralmente o registro.

#### Scenario: Desativação
- **WHEN** o Administrador confirma a desativação de uma especialidade ativa
- **THEN** o registro permanece persistido, passa a ser identificado como inativo e deixa de poder ser selecionado em novas associações

#### Scenario: Reativação
- **WHEN** o Administrador confirma a reativação de uma especialidade inativa
- **THEN** a especialidade volta a poder ser selecionada em novas associações

#### Scenario: Desistência antes de alterar situação
- **WHEN** o Administrador cancela ou fecha o diálogo de alteração de situação
- **THEN** nenhuma mutação é executada e os vínculos históricos são preservados

### Requirement: Administrador gerencia profissionais
O sistema MUST permitir cadastrar profissional com nome e e-mail único, com zero ou mais especialidades válidas, sem pedir identificador interno nem vínculo manual de conta. MUST gerar identificador interno único, sem simular CRM, e vincular exatamente uma identidade `MEDICO` válida no fluxo de cadastro médico. Edição legada MUST preservar vínculos existentes quando não alterados.

#### Scenario: Novo profissional válido
- **WHEN** um Administrador autenticado informa nome e e-mail válido, com zero ou mais especialidades ativas
- **THEN** o sistema cria exatamente um profissional ativo e a identidade Médica vinculada sem exigir identificador interno

#### Scenario: Identificador profissional duplicado
- **WHEN** a operação legada de domínio tenta cadastrar ou editar profissional com identificador interno já atribuído
- **THEN** o servidor rejeita a duplicidade sem alterar registros existentes

#### Scenario: Profissional sem especialidade
- **WHEN** o Administrador salva um novo médico sem selecionar especialidades
- **THEN** o cadastro e o vínculo único com a identidade Médica são persistidos sem associação de especialidade

#### Scenario: Cadastro médico novo
- **WHEN** o Administrador salva nome, e-mail e especialidades opcionais válidas
- **THEN** o sistema persiste profissional, conta MEDICO e associações atomicamente, gerando identificador interno e credencial temporária segura

#### Scenario: E-mail já cadastrado
- **WHEN** o e-mail normalizado pertence a conta de outra role ou Médico já vinculado
- **THEN** o servidor rejeita o cadastro sem alterar registros ou senhas existentes

#### Scenario: Conta Médica disponível
- **WHEN** o e-mail pertence a conta MEDICO sem vínculo
- **THEN** o servidor reutiliza essa identidade sem redefinir senha e cria associação única

#### Scenario: Falha na associação
- **WHEN** uma associação ou constraint falha durante o cadastro
- **THEN** nenhuma identidade órfã ou profissional parcial é persistido

#### Scenario: Edição sem especialidade
- **WHEN** o Administrador salva lista vazia na edição de um profissional
- **THEN** os vínculos atuais são removidos e o profissional permanece cadastrado

#### Scenario: Especialidades removidas na edição
- **WHEN** o Administrador desmarca todas as especialidades de um profissional existente
- **THEN** o sistema remove os vínculos válidos sem apagar o profissional ou alterar sua identidade de login

### Requirement: Relação entre profissionais e especialidades é muitos-para-muitos
O sistema MUST permitir que um profissional esteja associado a zero, uma ou várias especialidades e MUST permitir que uma especialidade esteja associada a vários profissionais.

#### Scenario: Profissional com múltiplas especialidades
- **WHEN** o Administrador seleciona duas ou mais especialidades ativas para um profissional
- **THEN** todas as associações são persistidas sem duplicidade

#### Scenario: Especialidade compartilhada
- **WHEN** dois profissionais diferentes são associados à mesma especialidade ativa
- **THEN** ambas as associações são aceitas e permanecem independentes

#### Scenario: Associação duplicada
- **WHEN** a mesma especialidade é enviada mais de uma vez para o mesmo profissional
- **THEN** o sistema mantém no máximo uma associação persistida para esse par

#### Scenario: Remover todas as especialidades
- **WHEN** um Administrador edita profissional e desmarca todas as especialidades
- **THEN** o profissional permanece válido e sem vínculos de especialidade

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
O sistema MUST oferecer páginas administrativas distintas para listagem, pesquisa, filtro de situação, paginação e operações de edição e ativação existentes. A listagem completa de especialidades MUST apresentar os registros autorizados em tabela semântica com colunas Especialidade, Situação e Ações, contagem dos resultados filtrados, busca combinada com situação, estados vazios adequados e opção de limpar filtros. O resumo recente do dashboard permanece distinto.

#### Scenario: Pesquisa sem resultado
- **WHEN** a pesquisa não encontra registros
- **THEN** a página apresenta estado vazio apropriado, sem apagar ou modificar dados

#### Scenario: Navegação e paginação
- **WHEN** o Administrador abre uma página completa e avança entre páginas
- **THEN** os controles informam estado atual e evitam navegação fora dos limites

#### Scenario: Combinar busca e situação
- **WHEN** o Administrador filtra o nome e seleciona a situação
- **THEN** a tabela apresenta somente a interseção dos registros persistidos, com contagem correta e retorno à primeira página

#### Scenario: Limpar filtros
- **WHEN** o Administrador limpa os filtros
- **THEN** busca e situação retornam ao padrão e a paginação volta a uma página válida

#### Scenario: Sem registros cadastrados
- **WHEN** a clínica não possui especialidades
- **THEN** a tela oferece o cadastro real sem exibir dados de exemplo como persistidos

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

### Requirement: Cadastro médico administrativo mantém um único fluxo acessível
As entradas de cadastro médico em Funcionários e Profissionais MUST reutilizar o mesmo State, formulários, serviços e regras de domínio. O modal de Profissionais MUST possuir título acessível, ação de fechamento, rótulos de campo, erros junto aos campos de identificação e especialidades opcionais com controle nativo, foco visível e navegação por teclado. O estado de envio de e-mail MUST refletir apenas o resultado efetivamente conhecido do provedor.

#### Scenario: Modal sem especialidades disponíveis
- **WHEN** o Administrador abre Novo profissional sem especialidades ativas disponíveis
- **THEN** o modal informa a ausência de opções e permite cadastrar sem vínculo

#### Scenario: Erro de nome ou e-mail
- **WHEN** o Administrador submete nome vazio, somente espaços ou e-mail inválido
- **THEN** o modal mantém valores corrigíveis e apresenta erro associado ao respectivo campo sem persistir registros

#### Scenario: Cancelamento e teclado
- **WHEN** o Administrador aciona Cancelar, o botão de fechar ou Escape sem submissão em andamento
- **THEN** o modal é fechado sem mutações, o foco retorna ao contexto de origem e a página principal torna-se interativa

#### Scenario: Sucesso e feedback real de e-mail
- **WHEN** o cadastro persiste, mas o provedor de e-mail não está configurado
- **THEN** a interface confirma o cadastro sem afirmar entrega de instruções

#### Scenario: Consistência entre entradas
- **WHEN** o cadastro médico é iniciado a partir de Funcionários ou Profissionais
- **THEN** as duas entradas submetem a mesma regra de unicidade, RBAC, validação e persistência, sem duplicações; o diretório reflete os dados reais

### Requirement: Diretório de especialidades filtra vínculos profissionais
O diretório completo de especialidades MUST apresentar um controle acessível de filtros adicionais que permita distinguir especialidades com e sem profissionais vinculados, usando as associações persistidas carregadas por operações autorizadas. Limpar filtros MUST restaurar a lista e a página inicial.

#### Scenario: Filtrar especialidades vinculadas
- **WHEN** um Administrador seleciona “Com profissionais” nos filtros adicionais
- **THEN** a lista mostra somente especialidades que possuem ao menos um vínculo persistido

#### Scenario: Filtrar especialidades sem vínculos
- **WHEN** um Administrador seleciona “Sem profissionais” nos filtros adicionais
- **THEN** a lista mostra somente especialidades sem vínculos profissionais persistidos

#### Scenario: Remover filtro de vínculos
- **WHEN** o Administrador seleciona “Todas” ou limpa os filtros
- **THEN** a lista volta a considerar todas as especialidades que correspondem à pesquisa e ao filtro de situação

### Requirement: Diretórios administrativos mostram a paginação real dos resultados
O diretório de especialidades e o diretório completo de profissionais MUST exibir a faixa atual de resultados, um seletor de tamanho de página e controles de página anterior/atual/próxima. O tamanho MUST aceitar somente 10, 25 ou 50 itens, usar os registros carregados sob a autorização administrativa existente e reiniciar em 1 quando o tamanho mudar.

#### Scenario: Alterar o tamanho da página
- **WHEN** um Administrador escolhe um tamanho de página permitido
- **THEN** o diretório volta à página 1 e exibe a faixa correspondente aos resultados filtrados

#### Scenario: Rejeitar tamanho inválido
- **WHEN** chega um tamanho fora de 10, 25 ou 50
- **THEN** o estado de paginação permanece inalterado

### Requirement: Diretório de especialidades preserva a composição desktop compacta
Na referência desktop de 1768×890, o painel do diretório MUST manter seis linhas completas da tabela e a paginação visível na primeira dobra quando houver mais resultados. A rolagem vertical MUST ficar limitada à tabela, conservar o cabeçalho visível e permitir navegação por teclado; o restante da página não pode ser cortado.

#### Scenario: Há mais de seis especialidades na primeira página
- **WHEN** o Administrador abre o diretório no viewport de referência e existem mais de seis resultados
- **THEN** as seis primeiras linhas aparecem completas, a faixa de resultados e a paginação permanecem visíveis e a rolagem da lista é acessível por teclado

### Requirement: Diretório completo de profissionais oferece tabela compacta e ações protegidas
O sistema MUST exibir os profissionais autorizados em tabela semântica com nome, e-mail, especialidades, situação profissional, acesso e ações, preservando operações acessíveis em mobile e diálogos existentes.

#### Scenario: Especialidades vinculadas
- **WHEN** um profissional possui múltiplas especialidades
- **THEN** o diretório mostra um resumo compacto e oferece consulta acessível aos vínculos persistidos

#### Scenario: Sem especialidade
- **WHEN** um profissional não possui especialidade vinculada
- **THEN** o diretório apresenta “Não vinculada”, sem dados inventados

#### Scenario: Busca e filtros combinados
- **WHEN** o Administrador pesquisa nome ou e-mail e seleciona filtros de situação e especialidade
- **THEN** a lista combina os critérios, mostra quantidade encontrada e reinicia a paginação

#### Scenario: Resultado vazio
- **WHEN** não existem profissionais compatíveis com a seleção
- **THEN** a página apresenta mensagem adequada e controle de limpeza dos filtros

#### Scenario: Editar em contexto
- **WHEN** o Administrador seleciona Editar em uma linha
- **THEN** o modal existente abre preenchido e salva mediante autorização e validação no servidor

#### Scenario: Confirmar alteração de situação
- **WHEN** o Administrador solicita desativação ou reativação
- **THEN** um diálogo identifica o profissional e exige confirmação antes da mutação

#### Scenario: Situação alterada em outra sessão
- **WHEN** o status persistido mudou desde a confirmação exibida
- **THEN** o servidor recusa a operação obsoleta, preserva o estado atual e apresenta feedback

#### Scenario: Conta distinta da situação profissional
- **WHEN** um profissional é desativado
- **THEN** seus vínculos são preservados e o sistema não altera automaticamente a conta de login

### Requirement: Estados de acesso e reemissão são apresentados com precisão
O sistema MUST diferenciar a situação operacional da situação de envio da credencial inicial. Uma requisição aceita pelo provedor MUST ser exibida apenas como aceita, nunca como entregue ao destinatário.

#### Scenario: Envio não configurado
- **WHEN** o estado persistido é `NOT_CONFIGURED`
- **THEN** o diretório informa que não foi enviado e oferece reemissão controlada quando elegível

#### Scenario: Falha ou estado indeterminado
- **WHEN** o estado persistido é `FAILED` ou `UNKNOWN`
- **THEN** o diretório não informa sucesso e exige confirmação explícita para gerar novo acesso

#### Scenario: Exceção de transporte na reemissão
- **WHEN** a chamada ao provedor falha sem confirmação de aceite
- **THEN** o sistema não repete automaticamente o envio nem afirma entrega

#### Scenario: Acesso não elegível para reemissão
- **WHEN** o profissional não tem conta elegível ou o onboarding já está concluído
- **THEN** o sistema não mostra uma ação de reemissão indevida

### Requirement: Edição e alternância de especialidades rejeitam estado obsoleto
O sistema MUST ler no servidor o registro de especialidade antes de abrir sua edição e MUST rejeitar edições e alterações de situação baseadas em um estado anterior ao persistido por outra transação, sem apagar o registro nem suas associações históricas.

#### Scenario: Edição iniciada a partir de listagem desatualizada
- **WHEN** o Administrador abre a edição de uma especialidade exibida no diretório
- **THEN** o formulário carrega o nome atual persistido no banco após autorização

#### Scenario: Outro usuário já renomeou a especialidade
- **WHEN** o Administrador tenta salvar a alteração com o nome original que já não corresponde ao registro persistido
- **THEN** o servidor rejeita a gravação, preserva o conteúdo digitado e informa que é necessário reabrir a edição

#### Scenario: A situação foi alterada por outra sessão
- **WHEN** o Administrador tenta desativar ou reativar a especialidade a partir de uma situação desatualizada
- **THEN** o servidor rejeita a operação sem reverter a alteração concorrente

### Requirement: Erros de especialidade aparecem no formulário e sucesso não ocupa a página
O sistema MUST apresentar erro de validação ou persistência junto ao campo do modal, preservando o valor e mantendo o diálogo aberto; MUST enviar confirmação compacta apenas após uma mutação persistida e atualizar a listagem de acordo com filtros vigentes.

#### Scenario: Cadastro inválido ou duplicado
- **WHEN** o servidor rejeita um cadastro de especialidade
- **THEN** o valor digitado permanece no modal, com mensagem associada ao campo, e não há sucesso

#### Scenario: Operação bem-sucedida
- **WHEN** cadastro, edição ou mudança de situação é confirmada no banco
- **THEN** a listagem é atualizada sem recarregar a página e um toast de sucesso é emitido
