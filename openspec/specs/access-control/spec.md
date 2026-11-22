# access-control Specification

## Purpose

Fornecer autenticação local e controle de acesso baseado em roles para identificar o usuário atual e proteger páginas, dados e ações do Vitta-One antes da implementação dos módulos de negócio.

## Requirements

### Requirement: Login local com credenciais válidas
O sistema MUST permitir que um usuário previamente cadastrado se autentique utilizando e-mail e senha válidos, MUST criar uma sessão autenticada associada à identidade e à role desse usuário e MUST apresentar o formulário de autenticação de forma utilizável em desktop, tablet, mobile e viewports de baixa altura.

#### Scenario: Credenciais válidas
- **WHEN** um usuário informa um e-mail cadastrado e a senha correspondente
- **THEN** o sistema autentica o usuário, cria a sessão e direciona para o shell de dashboard compatível com sua role

#### Scenario: Credenciais inválidas
- **WHEN** um usuário informa e-mail inexistente ou senha incorreta
- **THEN** o sistema não cria sessão autenticada e apresenta uma mensagem genérica de falha que não revela qual credencial está incorreta

#### Scenario: Login em viewport estreita ou baixa
- **WHEN** a tela de login é aberta em viewport que não comporta confortavelmente o layout dividido
- **THEN** o formulário permanece integralmente legível e alcançável, sem clipping de campos ou ação de entrada, e o conteúdo visual secundário é reduzido ou removido

### Requirement: Senhas não podem ser armazenadas em texto puro
O sistema MUST persistir somente uma representação criptograficamente segura da senha e MUST verificar a senha informada contra essa representação no lado servidor.

#### Scenario: Persistência de credencial
- **WHEN** uma credencial de usuário é criada ou alterada
- **THEN** nenhuma senha em texto puro é persistida no banco de dados, logs ou arquivos versionados

### Requirement: Sessão autenticada
O sistema MUST manter uma sessão autenticada suficiente para identificar o usuário e sua role durante a navegação e MUST revalidar a sessão no lado servidor antes de liberar dados ou ações protegidas.

#### Scenario: Recarregamento de página
- **WHEN** um usuário com sessão válida recarrega uma página protegida
- **THEN** o sistema restaura o contexto autenticado sem exigir novo login enquanto a sessão permanecer válida

#### Scenario: Sessão ausente ou inválida
- **WHEN** uma página, carregamento de dados ou ação protegida é solicitada sem uma sessão válida
- **THEN** o sistema nega o acesso e direciona o fluxo de interface para autenticação sem expor dados privados

### Requirement: Logout invalida a sessão
O sistema MUST permitir que um usuário autenticado encerre sua sessão e MUST impedir reutilização dessa sessão após o logout.

#### Scenario: Logout concluído
- **WHEN** um usuário autenticado executa logout
- **THEN** o sistema invalida a sessão atual, limpa o contexto autenticado e direciona para a página de login

### Requirement: Roles fixas do domínio
O sistema MUST reconhecer exatamente as roles Administrador, Recepcionista, Médico e Financeiro para controle de acesso nesta capability.

#### Scenario: Usuário autenticado possui uma role válida
- **WHEN** a sessão de um usuário autenticado é carregada
- **THEN** o sistema associa o usuário a uma das quatro roles previstas e usa essa role nas decisões de autorização

### Requirement: Autorização deve ser aplicada no servidor
O sistema MUST validar identidade e role no lado servidor em todo event handler, loader, computed var ou operação que leia ou modifique dados protegidos. Ocultar componentes ou redirecionar páginas no frontend MUST NOT ser considerado controle de acesso suficiente.

#### Scenario: Tentativa de ação sem permissão
- **WHEN** um usuário autenticado tenta acionar diretamente uma operação não permitida para sua role
- **THEN** o servidor rejeita a operação e nenhum dado protegido é criado, alterado, removido ou retornado indevidamente

### Requirement: Shell de dashboard por role
O sistema MUST possuir um destino inicial protegido para cada uma das quatro roles. Esses destinos MAY hospedar funcionalidades de negócio definidas por capabilities específicas, desde que cada operação continue submetida à autorização server-side correspondente.

#### Scenario: Administrador conclui login
- **WHEN** um usuário com role Administrador conclui a autenticação
- **THEN** o sistema direciona para o painel administrativo protegido

#### Scenario: Recepcionista conclui login
- **WHEN** um usuário com role Recepcionista conclui a autenticação
- **THEN** o sistema direciona para o painel de recepção protegido

#### Scenario: Médico conclui login
- **WHEN** um usuário com role Médico conclui a autenticação
- **THEN** o sistema direciona para o painel médico protegido

#### Scenario: Financeiro conclui login
- **WHEN** um usuário com role Financeiro conclui a autenticação
- **THEN** o sistema direciona para o painel financeiro protegido

### Requirement: Não existe cadastro público nesta change
O sistema MUST NOT expor um fluxo público de criação de contas como parte desta capability inicial.

#### Scenario: Visitante acessa a área pública
- **WHEN** uma pessoa não autenticada navega pela aplicação
- **THEN** o sistema oferece autenticação, mas não oferece criação pública de conta

### Requirement: Bootstrap controlado do primeiro Administrador
O sistema MUST fornecer um mecanismo de bootstrap manual, controlado e idempotente para criar o primeiro usuário Administrador quando ainda não existir um administrador, sem usar senha padrão hardcoded ou versionada.

#### Scenario: Primeiro bootstrap
- **WHEN** o bootstrap é executado com credenciais fornecidas por configuração segura e ainda não existe Administrador
- **THEN** o sistema cria exatamente um usuário Administrador com senha armazenada de forma segura

#### Scenario: Bootstrap repetido
- **WHEN** o bootstrap é executado novamente após já existir um Administrador correspondente
- **THEN** o sistema não cria uma conta duplicada nem substitui silenciosamente a credencial existente

### Requirement: Senha permanece mascarada com controle acessível de revelação
O campo de senha MUST iniciar mascarado e MUST permitir revelar ou ocultar o valor por um controle de ícone centralizado dentro da área do campo, sem alterar o valor digitado.

#### Scenario: Revelar senha
- **WHEN** o usuário aciona o controle de revelar senha
- **THEN** o valor permanece inalterado, o campo passa a exibi-lo e o controle comunica estado e nome acessível equivalentes a “Ocultar senha”

#### Scenario: Ocultar senha
- **WHEN** o usuário aciona novamente o controle
- **THEN** o campo volta a mascarar o valor e o controle comunica estado e nome acessível equivalentes a “Mostrar senha”

### Requirement: Subrotas administrativas conservam RBAC server-side
O sistema MUST validar sessão e role ADMINISTRADOR antes de disponibilizar conteúdo das rotas `/admin/especialidades` e `/admin/profissionais`, independentemente do estado da interface.

#### Scenario: Acesso sem sessão
- **WHEN** um visitante solicita diretamente uma das rotas de diretório
- **THEN** o acesso é negado e o usuário é direcionado para autenticação sem divulgar dados do diretório

#### Scenario: Acesso por outra role
- **WHEN** Médico, Recepcionista ou Financeiro solicita uma das rotas
- **THEN** a aplicação não apresenta a lista protegida e direciona para acesso negado

### Requirement: Senha inicial temporária impede acesso clínico antes de troca
O sistema MUST exigir troca de senha inicial temporária no primeiro login; MUST aplicar expiração da credencial, validar a senha nova e bloquear operações protegidas enquanto a troca não estiver concluída.

#### Scenario: Login com senha inicial válida
- **WHEN** Médico apresenta credencial temporária válida dentro do prazo
- **THEN** o servidor cria contexto provisório e direciona somente ao fluxo de troca obrigatória

#### Scenario: Tentativa de acesso direto a operação clínica
- **WHEN** a identidade Médica provisória chama uma operação server-side que exige role MEDICO
- **THEN** o servidor nega a operação sem acessar dados clínicos

#### Scenario: Senha inicial expirada
- **WHEN** Médico tenta autenticar usando senha inicial fora do prazo
- **THEN** a autenticação não libera acesso e comunica necessidade de reemissão administrativa

#### Scenario: Conclusão da troca
- **WHEN** Médico confirma a senha atual e escolhe nova senha válida
- **THEN** o hash é atualizado, o requisito de troca é removido e o acesso normal pode prosseguir

### Requirement: Rotas operacionais de Recepção exigem a role RECEPCIONISTA
O sistema MUST validar a sessão e a role RECEPCIONISTA no servidor antes de disponibilizar dados ou ações do dashboard, Agenda, Pacientes e Fila nas rotas `/recepcao`, `/recepcao/agenda`, `/recepcao/pacientes` e `/recepcao/fila`.

#### Scenario: Recepcionista abre uma rota operacional
- **WHEN** uma sessão válida de Recepcionista solicita diretamente uma das rotas da Recepção
- **THEN** o servidor valida a sessão e apresenta somente os dados e ações autorizados à role

#### Scenario: Outra role solicita uma rota de Recepção
- **WHEN** Médico, Administrador ou Financeiro solicita diretamente uma rota da Recepção
- **THEN** o servidor nega a leitura protegida e direciona para acesso negado

#### Scenario: Sessão expirada durante atualização
- **WHEN** uma atualização do dashboard é solicitada sem sessão válida
- **THEN** a aplicação limpa os dados protegidos e direciona para autenticação

### Requirement: Navegação administrativa distingue operações e inspeção local
O sistema MUST apresentar na central administrativa apenas links para rotas administrativas reais e autorizadas. A sidebar MUST distinguir destinos operacionais de visualizações locais de inspeção QA, que MUST permanecer indisponíveis quando o modo QA autorizado estiver desabilitado. Toda rota e operação MUST continuar exigindo autorização no servidor.

#### Scenario: Administrador navega nas tarefas da clínica
- **WHEN** um Administrador abre `/admin` e escolhe criar funcionário, consultar profissionais, especialidades, horários ou configurações
- **THEN** a navegação aponta para a rota implementada correspondente e mantém a indicação de página ativa

#### Scenario: Inspeção QA não habilitada
- **WHEN** um Administrador abre a sidebar sem o modo QA explicitamente autorizado
- **THEN** a navegação não oferece as rotas de inspeção local como tarefas operacionais

#### Scenario: Acesso direto indevido a visualização QA
- **WHEN** uma sessão sem permissão ou com modo QA desabilitado solicita diretamente uma rota de inspeção
- **THEN** o servidor nega a operação sem retornar dados clínicos protegidos

### Requirement: Navegação administrativa é utilizável em telas estreitas
O sistema MUST manter os destinos administrativos alcançáveis por teclado e sem overflow horizontal em viewport móvel. O controle de menu MUST informar o estado expandido e MUST permitir fechamento acessível.

#### Scenario: Administrador usa menu móvel
- **WHEN** o Administrador abre o menu em viewport estreita
- **THEN** o menu apresenta os destinos permitidos e um controle de fechamento alcançável pelo teclado, preservando foco visível

### Requirement: Ficha administrativa de funcionário persistido
O sistema MUST apresentar `/admin/funcionarios/[employee_id]` como consulta administrativa permanente e MUST projetar somente dados reais de funcionário autorizados no servidor. A interface MUST distinguir carregamento, registro não encontrado e falha recuperável, sem mostrar outro funcionário durante a navegação.

#### Scenario: Administrador consulta funcionário existente
- **WHEN** Administrador com sessão válida abre a ficha de um Médico ou Recepcionista cadastrado
- **THEN** a ficha mostra nome quando disponível, e-mail secundário, perfil em badge compacto e somente dados profissionais vinculados existentes, sem mensagem permanente de cadastro concluído

#### Scenario: Cadastro antigo sem nome
- **WHEN** a conta não possui nome persistido nem vínculo profissional com nome
- **THEN** a ficha indica “Nome não informado” e não trata o e-mail como nome fictício

#### Scenario: Registro inválido ou inexistente
- **WHEN** o identificador da rota não corresponde a funcionário elegível
- **THEN** a ficha apresenta estado de não encontrado e caminho de retorno à listagem

#### Scenario: Falha ao consultar funcionário
- **WHEN** a leitura autorizada falha por motivo operacional
- **THEN** o sistema limpa a projeção anterior, apresenta mensagem segura e oferece nova tentativa

#### Scenario: Sessão ausente ou role não autorizada
- **WHEN** alguém sem sessão válida ou com role diferente de Administrador tenta consultar a ficha diretamente
- **THEN** o servidor rejeita a consulta sem devolver dados de funcionário e a interface não libera o conteúdo protegido

### Requirement: Diretório administrativo de funcionários utiliza dados autorizados e identificação honesta
O sistema MUST disponibilizar ao Administrador um diretório consultável de contas internas que já sejam autorizadas pelo serviço de acesso. A interface MUST apresentar nome quando cadastrado, e-mail em campo próprio, perfil textual e ação acessível para consultar detalhes. O sistema MUST NOT apresentar e-mail como nome fictício quando o nome estiver ausente.

#### Scenario: Funcionário com nome cadastrado
- **WHEN** o Administrador consulta um registro com `display_name` persistido
- **THEN** o diretório exibe o nome como identificação principal e o e-mail em coluna separada

#### Scenario: Conta antiga sem nome
- **WHEN** o Administrador consulta uma conta sem `display_name`
- **THEN** o diretório declara “Nome não informado” e mantém o e-mail identificável sem inventar nome

#### Scenario: Busca combinada por perfil
- **WHEN** o Administrador procura por nome ou e-mail e escolhe um perfil permitido
- **THEN** a listagem apresenta apenas registros autorizados que correspondem simultaneamente à busca e ao perfil e reinicia a página de navegação

#### Scenario: Poucos registros
- **WHEN** o resultado filtrado cabe em uma única página
- **THEN** o total é informado e a interface não exibe controles de paginação desnecessários

#### Scenario: Diretório vazio, filtro sem resultados ou erro de leitura
- **WHEN** não existem funcionários, a pesquisa não corresponde a nenhum registro ou a consulta falha
- **THEN** o sistema apresenta o estado apropriado e oferece a ação permitida de cadastro, limpeza de filtros ou tentativa de nova leitura

#### Scenario: Acesso por perfil não autorizado ou sessão inválida
- **WHEN** uma pessoa sem sessão válida ou sem perfil Administrador tenta listar ou consultar a ficha de funcionários
- **THEN** o servidor nega a leitura e nenhuma informação da equipe é retornada

### Requirement: Gerenciamento autorizado de convites do portal
O gerenciamento de acesso MUST consultar o vínculo real da conta e o histórico persistido de convites, exigir consentimento explícito em cada solicitação e revalidar a autorização server-side. Convites MUST NOT duplicar conta ou expor código, hash ou senha.

#### Scenario: Consulta de situação do portal
- **WHEN** uma recepcionista autorizada abre o gerenciamento de acesso
- **THEN** a interface consulta a situação persistida e mostra o estado compatível, sem equiparar e-mail cadastrado a conta ativa

#### Scenario: Convite válido
- **WHEN** a recepcionista informa e-mail válido, confirma consentimento e solicita convite de paciente sem conta
- **THEN** o serviço aplica autorização e deduplicação e registra a tentativa; confirmação do provedor é comunicada somente como aceitação, não entrega

#### Scenario: Consentimento ausente ou e-mail já utilizado
- **WHEN** o consentimento não é confirmado ou o e-mail já pertence a outra conta/convite ativo
- **THEN** o servidor recusa a operação sem criar outra conta ou enviar mensagem

#### Scenario: Reenvio antecipado
- **WHEN** um convite ao mesmo paciente é solicitado antes de transcorrer 2 minutos
- **THEN** o serviço bloqueia novo convite e preserva o histórico e o vínculo

#### Scenario: Falha de envio ou acesso negado
- **WHEN** o provedor não aceita a mensagem ou a sessão não tem permissão
- **THEN** o sistema apresenta resultado fiel ou bloqueia a ação sem ativar acesso nem expor token

### Requirement: Cadastro interno unificado de funcionários
O sistema MUST oferecer ao Administrador autenticado uma página de cadastro com nome completo e e-mail obrigatórios e perfil limitado aos tipos de funcionário autorizados. O servidor MUST ignorar dados exclusivos de outros perfis e MUST impedir cadastro por outras roles. Não pode haver cadastro público.

#### Scenario: Cadastro de recepcionista
- **WHEN** Administrador informa nome válido, e-mail não utilizado e senha inicial conforme política existente
- **THEN** uma conta RECEPCIONISTA é persistida com o nome informado e a senha sob hash forte

#### Scenario: Nome ausente ou inválido
- **WHEN** uma tentativa de criação possui nome vazio, só espaços, inferior a 2 ou superior a 160 caracteres
- **THEN** a operação é rejeitada no servidor e nenhuma conta é criada

#### Scenario: Perfil ou sessão inválidos
- **WHEN** usuário sem role ADMINISTRADOR tenta cadastrar funcionário ou submete perfil não autorizado
- **THEN** o servidor nega a operação sem criar identidade ou atribuir privilégios

#### Scenario: Trocar perfil
- **WHEN** Administrador troca o perfil durante o cadastro
- **THEN** nome e e-mail são preservados; os campos específicos mudam sem enviar dados incompatíveis, e eventual perda de dados específicos exige confirmação

#### Scenario: E-mail duplicado ou submissão repetida
- **WHEN** duas tentativas tentam criar identidade com o mesmo e-mail normalizado
- **THEN** no máximo uma conta é persistida e a segunda recebe feedback recuperável

#### Scenario: Primeiro acesso médico sem Resend
- **WHEN** o médico é cadastrado mas o envio de instruções não é configurado ou confirmado
- **THEN** o cadastro é preservado e a interface informa o estado correto, sem alegar envio nem tentar criar a conta novamente

#### Scenario: Erro de entrada ou falha do servidor
- **WHEN** o cadastro falha sem persistir
- **THEN** a página mantém a identificação válida, apresenta erros associados aos campos e permite corrigir e reenviar

### Requirement: Shell autenticado expõe navegação contextual e acessível
O shell compartilhado MUST mostrar apenas destinos existentes e autorizados à role atual; MUST indicar qual destino está ativo com `aria-current="page"`; e MUST preservar a indicação hierárquica de Administração sem atribuir estado atual ao ancestral. O recolhimento desktop MUST preservar nomes acessíveis dos destinos.

#### Scenario: Administrador acessa ficha de funcionário
- **WHEN** o Administrador acessa `/admin/funcionarios/novo` ou a ficha de um funcionário
- **THEN** Funcionários permanece destacado como destino atual e o contexto de Administração permanece identificável

#### Scenario: Administrador acessa especialidades
- **WHEN** o Administrador acessa `/admin/especialidades`
- **THEN** Especialidades é o destino ativo, e Visão geral não recebe `aria-current="page"`

#### Scenario: Menu mobile é fechado por teclado
- **WHEN** a pessoa abre a navegação temporária e pressiona Escape
- **THEN** o drawer fecha, devolve o foco ao controle de abertura e libera a rolagem do conteúdo

#### Scenario: O menu é recolhido no desktop
- **WHEN** a pessoa recolhe a sidebar em viewport desktop
- **THEN** ícones de destinos autorizados e seus nomes acessíveis continuam disponíveis

### Requirement: Preview local não amplia permissões clínicas
As visualizações operacionais de QA no menu do Administrador MUST aparecer somente com a configuração autorizada e MUST permanecer separadas das funções administrativas normais. Sua presença MUST NOT conceder leitura ou mutação clínica de outras roles.

#### Scenario: QA desabilitado
- **WHEN** o Administrador navega sem o modo local de QA habilitado
- **THEN** o menu não oferece os destinos de preview e as rotas de preview continuam bloqueadas pelo servidor

#### Scenario: QA habilitado
- **WHEN** o Administrador autorizado navega com a configuração local de QA habilitada
- **THEN** o menu distingue o grupo de inspeção local das tarefas administrativas e não oferece operações clínicas como permissão administrativa
