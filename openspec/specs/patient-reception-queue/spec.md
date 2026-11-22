# patient-reception-queue Specification

## Purpose

Permitir que a Recepção registre pacientes e mantenha uma fila operacional priorizada, enquanto Médicos chamam e finalizam o próximo atendimento sem que o sistema execute triagem clínica ou altere automaticamente a gravidade informada.

## Requirements

### Requirement: Cadastro mínimo de paciente pela Recepção
O sistema MUST permitir que um usuário com role Recepcionista cadastre um paciente com nome e CPF válidos e telefone brasileiro opcional com DDD. O CPF MUST ser normalizado para persistência e MUST permanecer único. Um telefone preenchido MUST ser normalizado para dígitos e conter 10 ou 11 dígitos.

#### Scenario: Novo paciente válido
- **WHEN** uma Recepcionista autenticada informa nome e CPF válidos ainda não cadastrados, com ou sem telefone válido
- **THEN** o sistema cria exatamente um paciente e disponibiliza esse paciente para entrada na fila

#### Scenario: CPF inválido
- **WHEN** a Recepcionista informa um CPF que não possui formato e dígitos verificadores válidos
- **THEN** o sistema rejeita o cadastro sem persistir o paciente e apresenta erro associado ao campo

#### Scenario: CPF já cadastrado
- **WHEN** a Recepcionista tenta cadastrar um CPF já existente
- **THEN** o sistema não cria paciente duplicado e informa que o cadastro existente deve ser utilizado

#### Scenario: Telefone ausente ou inválido
- **WHEN** a Recepcionista deixa o telefone vazio ou informa um telefone preenchido com comprimento diferente de 10 ou 11 dígitos
- **THEN** o telefone ausente é aceito e o telefone inválido é rejeitado sem persistir o paciente

### Requirement: Busca rápida de pacientes pela Recepção
O sistema MUST permitir que uma Recepcionista autenticada localize cadastros por nome, telefone ou CPF e MUST retornar somente identificador, nome e telefone. A busca MUST exigir role Recepcionista, ter limite de resultados e MUST NOT expor prontuário ou conteúdo clínico.

#### Scenario: Paciente encontrado
- **WHEN** a Recepcionista busca um paciente persistido por nome, telefone ou CPF
- **THEN** o sistema retorna somente os campos mínimos de identidade e permite selecionar o cadastro existente

#### Scenario: Acesso incompatível
- **WHEN** uma pessoa sem role Recepcionista solicita a busca
- **THEN** o servidor nega o acesso antes de retornar dados do paciente

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

### Requirement: Preview local do Administrador navega pacientes persistidos com busca e paginação
Quando o modo local de QA do Administrador estiver explicitamente habilitado, a visualização de pacientes MUST apresentar somente pacientes persistidos, MUST oferecer uma única busca no topo por nome ou CPF mascarado e MUST paginar o conjunto filtrado sem inventar registros.

#### Scenario: Lista possui múltiplas páginas
- **WHEN** o conjunto filtrado ultrapassa o tamanho de página definido pela interface
- **THEN** a interface apresenta somente a página atual, informa página e total e permite navegar para páginas válidas

#### Scenario: Busca altera resultados
- **WHEN** o Administrador modifica a consulta de busca
- **THEN** o conjunto é filtrado por nome ou CPF mascarado e a navegação retorna para a primeira página

#### Scenario: Busca sem resultados
- **WHEN** nenhum paciente persistido corresponde à consulta
- **THEN** a interface apresenta estado de nenhum resultado sem simular pacientes

### Requirement: Preview local permite seleção contextual somente leitura
A visualização local de pacientes do Administrador MUST permitir selecionar no máximo um paciente por vez por meio de checkbox controlado e MUST apresentar contexto e ações somente leitura compatíveis com o modo QA.

#### Scenario: Selecionar paciente
- **WHEN** o Administrador marca o checkbox de um paciente
- **THEN** esse paciente passa a ser o único selecionado e a interface exibe seus dados disponíveis, histórico operacional persistido e ações somente leitura

#### Scenario: Selecionar outro paciente
- **WHEN** existe um paciente selecionado e o Administrador marca outro checkbox
- **THEN** a seleção anterior é substituída pela nova sem criar seleção em massa

#### Scenario: Limpar seleção
- **WHEN** o Administrador desmarca o paciente selecionado ou aciona “Limpar seleção”
- **THEN** o contexto de paciente é removido sem alterar qualquer dado persistido

#### Scenario: Permissões permanecem intactas
- **WHEN** o Administrador usa a barra contextual do preview
- **THEN** nenhuma ação exclusiva de Recepção ou Médico é disponibilizada ou executada e a autorização server-side existente permanece inalterada

### Requirement: Edição cadastral isolada na ficha de paciente
A Recepção MUST disponibilizar uma ação específica de edição cadastral, separada do convite de acesso e do agendamento. A interface MUST manter um rascunho independente até a persistência, atualizar nome e telefone autorizados e preservar CPF e vínculo com conta.

#### Scenario: Atualização válida
- **WHEN** a recepcionista autorizada altera o nome ou telefone e confirma o salvamento
- **THEN** o servidor valida a sessão, o paciente e os campos, persiste os valores e a ficha exibe os dados atualizados

#### Scenario: Formulário inválido
- **WHEN** nome é vazio/composto por espaços ou telefone informado é inválido
- **THEN** o servidor rejeita a alteração, a interface mantém os valores digitados e apresenta mensagem de erro contextual

#### Scenario: Cancelamento
- **WHEN** a recepcionista fecha o modal antes de salvar
- **THEN** o cadastro persistido permanece inalterado e a ficha não exibe valores provisórios

#### Scenario: Estado ou identidade adulterados
- **WHEN** a sessão perde a autorização ou o identificador de paciente não corresponde à ficha aberta
- **THEN** nenhuma alteração é persistida e a operação é rejeitada

### Requirement: O diretório da Recepção abre a ficha do paciente da linha selecionada
A lista de pacientes da Recepção MUST gerar a ação de detalhes a partir do identificador persistido da mesma linha que apresenta nome e telefone. Após ativar a ação, a rota e a ficha carregada MUST representar essa identidade e MUST continuar sujeitas à autorização server-side da Recepção.

#### Scenario: Abrir detalhes de um resultado da busca
- **WHEN** uma Recepcionista autenticada pesquisa pacientes e ativa “Ver detalhes” em uma linha
- **THEN** a rota de destino usa o identificador persistido dessa linha e a ficha exibe o nome do mesmo cadastro

#### Scenario: Sessão ou role sem acesso
- **WHEN** a sessão expira ou uma identidade sem role Recepcionista solicita a rota da ficha
- **THEN** o servidor nega o acesso conforme a autorização existente e não retorna dados do paciente

### Requirement: O diretório permite filtrar a disponibilidade de telefone e escolher o tamanho da página
A interface MUST oferecer um filtro recolhível de disponibilidade de telefone e tamanhos de página de 10, 20 e 30 registros. A busca, o filtro e a paginação MUST continuar aplicados no servidor após revalidar a role Recepcionista; alterar busca, filtro ou tamanho MUST reiniciar na primeira página.

#### Scenario: Filtrar cadastros com telefone
- **WHEN** uma Recepcionista escolhe “Com telefone” no painel “Mais filtros”
- **THEN** o servidor retorna somente pacientes persistidos com telefone não vazio e atualiza a contagem autorizada

#### Scenario: Filtrar cadastros sem telefone
- **WHEN** uma Recepcionista escolhe “Sem telefone” no painel “Mais filtros”
- **THEN** o servidor retorna somente pacientes persistidos sem telefone e preserva a pesquisa textual aplicada

#### Scenario: Ajustar tamanho da página
- **WHEN** uma Recepcionista seleciona 20 ou 30 itens por página
- **THEN** o servidor busca o tamanho solicitado, recalcula o total de páginas e exibe a primeira página

### Requirement: Diretório operacional protegido de pacientes da Recepção
O sistema MUST oferecer à role Recepcionista uma listagem compacta dos pacientes persistidos com nome, telefone quando cadastrado e ação explícita de navegação à ficha individual. A leitura MUST revalidar a sessão e a role no servidor, MUST NOT incluir CPF em claro nem conteúdo clínico na projeção e MUST utilizar paginação persistente com ordenação determinística.

#### Scenario: Lista de pacientes cadastrados
- **WHEN** a Recepcionista autenticada acessa a página de pacientes
- **THEN** o sistema exibe somente pacientes persistidos, em tabela semântica com navegação "Ver detalhes" para a ficha autorizada

#### Scenario: Página com múltiplos registros
- **WHEN** a base possui mais registros que o tamanho de página
- **THEN** o servidor retorna somente a página solicitada, total real e ordenação estável por nome e identificador

#### Scenario: Página única
- **WHEN** os resultados cabem em uma página
- **THEN** a interface informa a quantidade com singular ou plural correto e oculta os controles de paginação

#### Scenario: Busca contextual
- **WHEN** a Recepcionista submete um nome, CPF ou telefone
- **THEN** o servidor normaliza a entrada, filtra somente registros autorizados e retorna à primeira página sem consultar a cada tecla

#### Scenario: Pesquisa vazia ou sem resultados
- **WHEN** a pesquisa não encontra resultados ou ainda não existem pacientes
- **THEN** a interface distingue esses estados e permite limpar a pesquisa ou iniciar o cadastro já existente

#### Scenario: Falha ao carregar
- **WHEN** a consulta falha por motivo operacional
- **THEN** os resultados desatualizados deixam de ser exibidos e a interface mostra mensagem acessível e ação para tentar novamente

#### Scenario: Sessão expirada ou role incompatível
- **WHEN** uma sessão expira ou um usuário de outro perfil solicita a listagem
- **THEN** o servidor nega a leitura, limpa os dados pessoais armazenados no State e direciona para o fluxo de autenticação ou acesso negado

#### Scenario: Responsividade e teclado
- **WHEN** a Recepcionista usa um dispositivo de largura reduzida ou navega por teclado
- **THEN** nome, contato e ação principal permanecem utilizáveis sem transbordo horizontal do documento, com labels e foco visível

### Requirement: Ficha operacional autorizada do paciente
A Recepção SHALL consultar na ficha individual somente identidade e registros operacionais de um paciente persistido, incluindo CPF mascarado, telefone opcional, consultas futuras e anteriores, entrada ativa e movimentações encerradas na fila. O servidor SHALL revalidar a sessão e a role antes de cada leitura e não SHALL retornar sintomas, diagnósticos, prescrições ou outras informações clínicas dessa projeção.

#### Scenario: Recepcionista abre paciente existente
- **WHEN** uma recepcionista autenticada abre a ficha de um paciente persistido
- **THEN** o sistema mostra identificação mascarada, próximas consultas, situação da fila e histórico limitado aos registros desse paciente
- **AND** não envia CPF completo nem campos clínicos à interface

#### Scenario: Paciente inexistente ou acesso indevido
- **WHEN** o ID da rota é inválido, o paciente não existe ou a sessão não está autorizada
- **THEN** o sistema não revela dados pessoais
- **AND** apresenta um estado não encontrado ou redireciona para autenticação/acesso negado conforme o caso

#### Scenario: Histórico grande ou ausência de dados
- **WHEN** o paciente possui mais de seis consultas anteriores
- **THEN** a Recepção pode navegar pelas páginas do histórico ordenadas por data
- **AND** um paciente sem registros recebe mensagens vazias específicas por seção

### Requirement: Identificação da entrada ativa da fila
A ficha SHALL distinguir entradas ativas de entradas encerradas, sem alterar prioridade ou ordenação clínica.

#### Scenario: Paciente com entrada ativa
- **WHEN** o paciente possui entrada AGUARDANDO ou EM_ATENDIMENTO
- **THEN** a ficha mostra situação, prioridade e horário de entrada
- **AND** oferece acesso à fila sem exibir ação para adicionar uma nova entrada

#### Scenario: Entrada avulsa duplicada
- **WHEN** duas operações tentam adicionar o mesmo paciente com entrada ativa à fila avulsa
- **THEN** o serviço impede a duplicação sob serialização transacional no PostgreSQL
- **AND** não altera a prioridade da entrada existente

#### Scenario: Check-in agendado com fila ativa
- **WHEN** uma consulta agendada tenta confirmar chegada enquanto o mesmo paciente possui entrada ativa na fila
- **THEN** o serviço recusa criar outra entrada, preservando o estado da consulta e a prioridade existente
- **AND** uma nova confirmação poderá ser realizada após encerramento legítimo da entrada anterior

#### Scenario: Paciente com somente entradas encerradas
- **WHEN** um paciente possui apenas entradas FINALIZADO ou RETIRADO
- **THEN** a ficha mostra que não existe entrada ativa
- **AND** permite iniciar o fluxo de nova entrada com as validações de domínio existentes

### Requirement: Formulário dedicado de cadastro oferece entrada acessível e validação recuperável
O formulário de novo paciente da Recepção MUST manter nome e CPF obrigatórios, telefone opcional, máscara automática de CPF e feedback específico por campo. A UI MUST permitir colar CPF com ou sem pontuação, MUST preservar os valores editados em erro de validação e MUST apresentar o primeiro campo inválido com foco e erro associado programaticamente. A interface MUST usar componentes existentes, ter largura controlada e funcionar por teclado e em telas estreitas.

#### Scenario: Recepcionista digita ou cola CPF sem pontuação
- **WHEN** a Recepcionista preenche CPF válido com 11 dígitos, digitado ou colado
- **THEN** o campo mostra a formatação visual sem exigir pontuação manual, e o servidor valida os mesmos 11 dígitos para persistência

#### Scenario: Dados inválidos são corrigidos no próprio formulário
- **WHEN** a Recepcionista envia nome vazio ou só com espaços, CPF inválido ou telefone inválido preenchido
- **THEN** o servidor rejeita o cadastro, o formulário identifica os campos com erro e mantém os valores para correção sem criar paciente

#### Scenario: Telefone opcional
- **WHEN** a Recepcionista não informa telefone e apresenta nome e CPF válidos
- **THEN** o cadastro pode ser concluído sem telefone

### Requirement: Cadastro de paciente confirma persistência e impede duplicação
A ação de cadastrar paciente MUST validar autorização e entrada no servidor, MUST impedir duas submissões simultâneas pelo State e MUST respeitar a unicidade de CPF no banco, inclusive sob concorrência. Sucesso MUST ser informado somente após persistência confirmada, seguido de navegação à ficha individual do paciente criado. Uma falha posterior de navegação MUST NOT provocar outra inserção automática.

#### Scenario: Cadastro válido encaminha à ficha
- **WHEN** uma Recepcionista autorizada confirma um cadastro válido de CPF ainda inexistente
- **THEN** exatamente um paciente é persistido, sua identificação é preservada e a ficha correspondente é aberta automaticamente

#### Scenario: CPF já cadastrado
- **WHEN** a Recepcionista tenta cadastrar um CPF que já pertence a um paciente
- **THEN** nenhum segundo registro é criado, a tela informa a duplicidade e pode oferecer acesso à ficha existente somente se o servidor autorizar sua consulta

#### Scenario: Cliques repetidos
- **WHEN** a Recepcionista envia o formulário novamente enquanto a operação anterior está em andamento ou após sucesso persistido na mesma tela
- **THEN** o State não emite outra inserção e mantém a identificação do cadastro confirmado

#### Scenario: Persistência confirmada seguida de falha na navegação
- **WHEN** a persistência do cadastro é confirmada, mas o redirecionamento não conclui
- **THEN** o State mantém o ID criado e disponibiliza um caminho para abrir a ficha sem criar novo paciente

#### Scenario: Sessão inválida ou role incompatível
- **WHEN** alguém sem sessão válida ou sem role Recepcionista tenta executar o cadastro diretamente
- **THEN** o servidor nega a operação sem expor dados pessoais ou persistir novos registros

### Requirement: Fila ativa exibe projeção operacional responsiva e mantém ordenação clínica
A Recepção MUST consultar apenas entradas em AGUARDANDO, apresentando prioridade textual, paciente, horário de entrada no fuso da clínica, tempo decorrido, situação e ações permitidas. Em desktop MUST usar tabela semântica e no celular MUST manter identificação, prioridade e ações sem overflow. Busca por nome e filtro de prioridade MUST restringir somente dados autorizados e MUST manter a ordenação calculada no servidor. Falha de consulta MUST NOT ser apresentada como fila vazia.

#### Scenario: Fila preenchida
- **WHEN** a Recepcionista carrega dados de pacientes aguardando
- **THEN** a UI apresenta a sequência do servidor, prioridade textual, espera derivada do instante persistido e ações autorizadas

#### Scenario: Busca sem resultados
- **WHEN** os filtros selecionados não correspondem a entradas
- **THEN** a UI apresenta mensagem distinta de fila vazia e permite limpar filtros

#### Scenario: Falha de consulta
- **WHEN** a leitura da fila não pode ser concluída
- **THEN** a UI apresenta erro recuperável e não declara que a fila está vazia

### Requirement: Inclusões avulsas e check-in impedem duplicidade de entrada ativa
O sistema MUST impedir que um mesmo paciente tenha duas entradas simultâneas em AGUARDANDO ou EM_ATENDIMENTO, independentemente de chegada agendada ou avulsa. O servidor MUST serializar as tentativas concorrentes de entrada com bloqueio transacional por paciente no PostgreSQL. Uma entrada RETIRADA ou FINALIZADA MUST permitir nova chegada.

#### Scenario: Dupla submissão
- **WHEN** uma recepcionista tenta incluir novamente um paciente com entrada ativa
- **THEN** a segunda operação falha sem criar outro registro

#### Scenario: Inclusões concorrentes
- **WHEN** check-in e inclusão avulsa são iniciados simultaneamente para um mesmo paciente
- **THEN** no máximo uma nova entrada ativa é persistida

#### Scenario: Nova visita
- **WHEN** a entrada anterior foi retirada ou concluída
- **THEN** uma nova entrada válida pode ser criada
