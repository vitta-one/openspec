## MODIFIED Requirements

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
