## ADDED Requirements

### Requirement: Recepção mantém cadastro operacional
A Recepção MUST pesquisar, abrir e atualizar nome/telefone de pacientes existentes e criar novos cadastros, validando CPF e contato no servidor e tratando CPF duplicado/conflitos concorrentes sem duplicar.

#### Scenario: Atualização concorrente
- **WHEN** duas operações atualizam o mesmo paciente
- **THEN** a última atualização válida preserva integridade e não altera o vínculo de portal

### Requirement: Portal é opcional e depende de consentimento
Criar paciente MUST NOT criar conta de portal automaticamente. Uma ação separada MUST exigir e-mail válido e consentimento explícito antes de emitir ou reemitir convite.

#### Scenario: Cadastro sem consentimento
- **WHEN** a Recepção cadastra paciente sem consentimento
- **THEN** o cadastro existe sem usuário nem convite de portal

#### Scenario: Envio indisponível
- **WHEN** e-mail não está configurado, falha ou fica indeterminado
- **THEN** paciente permanece cadastrado sem conta ativa, a tela mostra estado operacional honesto e nenhum segredo é apresentado

### Requirement: Dados clínicos permanecem inacessíveis à Recepção
Leituras/alterações de cadastro e agenda MUST NOT acessar ou retornar ClinicalCareRecord, Prescription ou texto clínico.

#### Scenario: Recepção consulta paciente
- **WHEN** a Recepção abre o cadastro operacional
- **THEN** vê somente identidade/contato/status de portal necessário à operação
