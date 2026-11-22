# patient-directory Specification

## Purpose

Especificar o cadastro e a ficha operacional de pacientes usados pela Recepção, separados do gerenciamento de fila e sem conceder acesso a diagnósticos, prescrições ou prontuário.

## Requirements

### Requirement: Cadastro de paciente utiliza identidade válida e única
O sistema MUST permitir ao perfil RECEPCIONISTA criar paciente com nome e CPF válidos, normalizar CPF e validar eventual telefone, mantendo unicidade e evitando persistência parcial.

#### Scenario: Cadastro válido
- **WHEN** a Recepção envia os dados mínimos válidos de paciente ainda não cadastrado
- **THEN** a aplicação cria um único Patient persistido e disponibiliza sua ficha

#### Scenario: CPF repetido ou inválido
- **WHEN** CPF é inválido ou já está cadastrado
- **THEN** o servidor rejeita a operação sem duplicar paciente e informa erro associado ao campo

#### Scenario: Formulário inválido
- **WHEN** algum campo informado não respeita tamanho ou formato permitido
- **THEN** o formulário mantém os valores úteis e mostra feedback recuperável sem gravar registro parcial

### Requirement: Diretório da Recepção aplica filtros e paginação autorizados
O sistema MUST apresentar lista de pacientes persistidos com busca por identidade e paginação estável, sem carregar texto clínico, credenciais ou dados de convite na projeção.

#### Scenario: Pesquisa por nome ou CPF
- **WHEN** a Recepcionista submete busca válida e altera filtros disponíveis
- **THEN** o servidor retorna somente pacientes correspondentes, com contagem e estado vazio honestos

#### Scenario: Navegação para ficha
- **WHEN** a Recepcionista seleciona a linha de um paciente persistido
- **THEN** o destino utiliza o ID daquela mesma linha e carrega o paciente correspondente

#### Scenario: Busca sem resultados
- **WHEN** não há correspondências
- **THEN** a UI mostra estado vazio sem reutilizar resultado de pesquisa anterior

### Requirement: Ficha apresenta histórico operacional minimizado
O sistema MUST projetar para a Recepção apenas identidade permitida, consultas e movimentações de fila operacionalmente necessárias, sem expor ClinicalCareRecord ou conteúdo prescrito.

#### Scenario: Paciente possui agendamentos e filas
- **WHEN** a Recepcionista acessa a ficha de Patient existente
- **THEN** o serviço retorna resumo de agendamentos, estados e entradas operacionais permitidos e dados formatados no fuso da clínica

#### Scenario: Paciente não possui histórico
- **WHEN** não há agendamentos ou entradas de fila para o paciente
- **THEN** a interface apresenta zero/estado vazio, sem fabricar consultas

#### Scenario: Consulta a outra ficha por ID
- **WHEN** a requisição altera patient_id ou tenta executar evento com sessão sem autorização
- **THEN** o servidor revalida role, existência e contexto antes de retornar dados

### Requirement: Edição cadastral preserva integridade e autorizações
O sistema MUST permitir apenas alterações cadastrais implementadas pelo fluxo de Recepção, validando formato e unicidade no servidor e sem alterar dados de consulta ou fila.

#### Scenario: Edição válida
- **WHEN** a Recepcionista salva dados cadastrais válidos em ficha existente
- **THEN** o servidor atualiza somente os campos autorizados e apresenta os novos dados

#### Scenario: Edição inválida ou duplicada
- **WHEN** os dados novos não são válidos ou violam unicidade de CPF
- **THEN** a alteração falha e mantém o valor anterior, com mensagem recuperável
