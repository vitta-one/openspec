## MODIFIED Requirements

### Requirement: A tabela do dia usa consultas reais no fuso da clínica
O sistema MUST listar as consultas persistidas cujo horário cai no dia atual do fuso configurado da clínica, ordenadas por horário e identificador. MUST incluir todos os estados persistidos, inclusive canceladas, sem inventar horários, disponibilidade ou dados de paciente.

#### Scenario: Limites do dia local
- **WHEN** consultas existem antes, dentro e depois do intervalo local convertido para UTC
- **THEN** somente as consultas dentro do intervalo local aparecem, em ordem estável

#### Scenario: Cancelamento persistido
- **WHEN** uma Consulta do dia está CANCELADA
- **THEN** ela continua visível com status cancelado e entra na contagem total exibida

### Requirement: A tabela limita dados à operação da Recepção
Cada linha MUST mostrar horário, nome e telefone do paciente, profissional, especialidades ativas associadas ao profissional, situação persistida e acesso à Agenda. A projeção MUST NOT ler ou expor relatos, diagnóstico, prescrição, prioridade, prontuário ou notas clínicas. O CPF pode ser usado para busca, mas MUST NOT aparecer na tabela.

#### Scenario: Telefone ou especialidade ausente
- **WHEN** o paciente não tem telefone ou o profissional não tem especialidade ativa
- **THEN** a tabela informa o dado ausente e preserva as outras informações da consulta

#### Scenario: Várias especialidades ativas
- **WHEN** o profissional tem mais de uma especialidade ativa
- **THEN** todas aparecem como associações do profissional, sem atribuir uma delas especificamente à Consulta

### Requirement: Busca, filtro e paginação operam no servidor
A interface MUST permitir busca contextual por nome, telefone ou CPF e filtro por profissional nas consultas do dia. A busca, filtro e paginação MUST ser aplicados no SQL antes de serializar os registros. Cada página MUST conter até sete consultas e informar contagem real. Nova busca ou troca de profissional MUST reiniciar na primeira página.

#### Scenario: Busca por telefone formatado
- **WHEN** a Recepcionista busca telefone com ou sem pontuação
- **THEN** o sistema normaliza a entrada e retorna somente consultas do dia associadas ao paciente correspondente

#### Scenario: Última página reduzida
- **WHEN** a última página tem menos de sete consultas
- **THEN** somente os registros restantes são exibidos e a navegação para a próxima página fica indisponível

#### Scenario: Total diminui durante navegação
- **WHEN** uma atualização reduz o total enquanto uma página posterior está aberta
- **THEN** o sistema ajusta a página para a última página válida

### Requirement: A página e suas leituras permanecem protegidas
O dashboard MUST permanecer protegido para a role Recepcionista e cada leitura MUST revalidar a sessão no servidor. Os links para ações continuam nos módulos existentes, sem criar fluxos paralelos.

#### Scenario: Leitura por outra role
- **WHEN** uma sessão sem role Recepcionista solicita a projeção
- **THEN** o servidor nega a leitura antes de retornar nome, telefone ou consultas

### Requirement: A tabela se adapta a teclado e telas estreitas
A tela MUST manter labels acessíveis e foco visível na busca, filtro, paginação e ações. Em viewports estreitas, a tabela pode rolar horizontalmente dentro de uma região identificada, sem causar overflow no documento.

#### Scenario: Tela estreita
- **WHEN** a viewport não comporta as colunas
- **THEN** elas permanecem disponíveis em uma área de rolagem nomeada e o restante da página não transborda
