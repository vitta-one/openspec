# admin-qa-patient-dossier Specification

## ADDED Requirements

### Requirement: Diretório de pacientes exclusivamente de consulta
O sistema MUST disponibilizar a listagem em `/admin/pacientes` apenas quando a flag de preview QA local estiver ativa e a sessão pertencer ao Administrador. A listagem MUST oferecer busca, paginação e ação "Ver detalhes" sem controles de seleção em lote nem históricos expandidos; MUST retornar à UI somente nome, ID e CPF mascarado.

#### Scenario: Administrador consulta a listagem autorizada
- **WHEN** Administrador autenticado acessa a listagem com preview QA habilitado
- **THEN** vê tabela compacta paginada, busca e acesso à ficha, sem dados clínicos

#### Scenario: Preview desabilitado ou papel inadequado
- **WHEN** uma leitura da listagem ocorre sem flag QA ou role autorizada
- **THEN** a leitura é recusada no servidor antes de transmitir dados pessoais

### Requirement: Ficha individual protege o recurso
O sistema MUST disponibilizar a ficha somente leitura em rota Reflex individual e MUST revalidar sessão, QA local, role e existência do paciente a cada carregamento. O identificador de URL MUST NOT ampliar autorização nem retornar dados de outro paciente.

#### Scenario: Acesso direto autorizado
- **WHEN** o Administrador abre uma ficha existente com QA local habilitado
- **THEN** o servidor retorna apenas identificação mascarada e entradas operacionais daquele paciente em horário local

#### Scenario: ID inexistente ou inválido
- **WHEN** a URL aponta para um ID ausente, inválido ou não positivo
- **THEN** o sistema apresenta "Paciente não encontrado" sem mostrar dados anteriores

### Requirement: Histórico clínico é projeção restrita e sob demanda
O sistema MUST carregar histórico clínico somente após solicitação explícita na ficha, utilizando a autorização QA e a projeção existente de atendimentos concluídos. O Administrador MUST NOT obter acesso clínico irrestrito de produção ou mutações por essa navegação.

#### Scenario: Consulta clínica QA
- **WHEN** o Administrador autorizado seleciona histórico clínico de paciente existente
- **THEN** o servidor revalida autorização e retorna somente registros concluídos permitidos no preview

#### Scenario: Volta ao histórico operacional
- **WHEN** o usuário seleciona histórico operacional
- **THEN** a projeção clínica previamente carregada é descartada do State e nenhuma ação de mutação é oferecida

#### Scenario: Sessão expirada
- **WHEN** a sessão deixa de ser válida entre abertura da ficha e consulta clínica
- **THEN** o servidor recusa a leitura e direciona para autenticação sem devolver prontuário
