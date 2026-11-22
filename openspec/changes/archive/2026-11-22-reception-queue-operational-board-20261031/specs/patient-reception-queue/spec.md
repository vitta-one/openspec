## ADDED Requirements

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
