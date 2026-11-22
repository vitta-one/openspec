# administration-dashboard Specification

## Purpose

Apresentar ao Administrador indicadores operacionais derivados de registros persistidos e acesso direto às tarefas administrativas autorizadas.

## Requirements

### Requirement: Painel administrativo mostra indicadores persistidos e definidos
O painel `/admin` MUST apresentar contagens de profissionais ativos, especialidades ativas, consultas não canceladas do dia no fuso da clínica e contas de equipe com perfil Médico ou Recepcionista. A projeção MUST ser autorizada para Administrador no servidor e MUST conter apenas agregados, sem dados de pacientes ou conteúdo clínico.

#### Scenario: Clínica sem registros
- **WHEN** não há profissionais, especialidades, consultas nem contas de equipe
- **THEN** cada indicador mostra zero e os atalhos administrativos continuam disponíveis

#### Scenario: Limite de data local
- **WHEN** consultas existem antes, dentro e depois do dia atual convertido do fuso da clínica para UTC
- **THEN** o indicador conta somente consultas não canceladas dentro do dia local

#### Scenario: Especialidades e profissionais inativos
- **WHEN** existem registros ativos e inativos nos diretórios
- **THEN** os indicadores de profissionais e especialidades contam somente registros ativos, enquanto contas de equipe contam os perfis cadastrados existentes

#### Scenario: Acesso sem perfil administrativo
- **WHEN** uma sessão sem role Administrador solicita os indicadores diretamente
- **THEN** o servidor nega a projeção antes de retornar qualquer contagem

### Requirement: Atalhos do painel levam a tarefas administrativas existentes
O painel MUST apresentar caminhos utilizáveis para diretório de profissionais, especialidades, horários, configurações e criação/listagem de funcionários. Cada destino MUST ser uma rota registrada e protegida pela autorização correspondente.

#### Scenario: Atalho de tarefa
- **WHEN** Administrador aciona um atalho do painel
- **THEN** a aplicação navega à tela administrativa existente para a tarefa identificada

#### Scenario: Sessão sem autorização
- **WHEN** outra role solicita diretamente um destino administrativo
- **THEN** a autorização server-side existente nega o conteúdo protegido
