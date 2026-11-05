## ADDED Requirements

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
