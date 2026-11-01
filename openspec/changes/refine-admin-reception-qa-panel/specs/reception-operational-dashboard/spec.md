# reception-operational-dashboard Specification

## ADDED Requirements

### Requirement: O preview administrativo em QA apresenta a operação da Recepção somente leitura
O sistema MUST disponibilizar `/admin/recepcao` apenas quando a flag local de QA estiver habilitada e a sessão válida pertencer ao Administrador. Cada recarga MUST revalidar a autorização no servidor antes de ler dados de pacientes, fila ou consultas. O preview MUST NOT disponibilizar eventos de criação, reavaliação, chamada, finalização, confirmação de chegada, cancelamento ou reagendamento.

#### Scenario: Acesso administrativo em QA
- **WHEN** o preview local está habilitado e uma sessão Administrador válida carrega a página
- **THEN** o sistema exibe uma projeção persistida somente leitura com identificação do modo QA

#### Scenario: Flag desativada ou sessão sem autorização
- **WHEN** a flag QA está desabilitada, a sessão expirou ou a role não é Administrador
- **THEN** a leitura é negada antes de retornar qualquer dado operacional protegido

### Requirement: Estado atual, histórico e agenda mantêm critérios temporais verificáveis
O preview MUST distinguir `AGUARDANDO` e `EM_ATENDIMENTO` atuais de `FINALIZADO` e `RETIRADO` por seus respectivos momentos de transição. As consultas MUST refletir registros agendados persistidos, com filtro de período em datas locais da clínica, profissional e situação registrada, sem inferir mudanças ou inventar horários. O preview MUST preservar a ordenação clínica já implementada para a fila aguardando e não pode alterar prioridade.

#### Scenario: Fila ativa e histórico coexistem
- **WHEN** há entradas aguardando e retiradas no banco
- **THEN** apenas aguardando e em atendimento compõem a fila ativa, enquanto retiradas aparecem no histórico do período

#### Scenario: Histórico cruza meia-noite UTC
- **WHEN** um evento é persistido em UTC e pertence ao dia local selecionado
- **THEN** a projeção inclui esse evento no dia local, exibe a hora no fuso da clínica e não transforma o instante armazenado

#### Scenario: Agenda sem consultas
- **WHEN** a consulta ao banco termina com sucesso e o período não possui consultas
- **THEN** o preview indica ausência de consultas para o período, não uma funcionalidade futura

#### Scenario: Falha na leitura
- **WHEN** o banco ou a projeção falha
- **THEN** o preview mostra erro contextual e não apresenta a falha como lista vazia

### Requirement: O preview transmite somente informação operacional mínima
A projeção MUST NOT expor CPF, relatos de sintomas, anamnese, diagnóstico, prescrição ou informação financeira. A agenda administrativa MUST conter apenas profissional, data/hora e situação. A página MUST permitir filtrar por período, prioridade e situação e limitar as listas sem falsificar contagens.

#### Scenario: Registro de fila contém sintomas
- **WHEN** a fila persistida contém relato clínico na entrada
- **THEN** a projeção da página não serializa o relato e identifica apenas paciente, prioridade, situação, horário e profissional pertinente

#### Scenario: Consulta com paciente cadastrado
- **WHEN** uma consulta é exibida na agenda administrativa
- **THEN** nenhum identificador ou dado clínico do paciente é enviado à lista da agenda

#### Scenario: Filtro aplicado
- **WHEN** o Administrador seleciona prioridade, situação ou período válido
- **THEN** os conjuntos exibidos e os indicadores aplicáveis refletem o filtro sem atribuir registros históricos à fila ativa
