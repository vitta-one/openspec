## Purpose

Permitir que exames e anexos clínicos sejam registrados no prontuário com armazenamento privado, rastreabilidade e acesso limitado ao vínculo assistencial ou ao próprio paciente.

## ADDED Requirements

### Requirement: Anexo clínico possui contexto e metadados persistidos
O sistema MUST vincular cada anexo a um Paciente e, quando aplicável, à Consulta e ao Atendimento correspondentes; MUST persistir título, categoria, data clínica, nome original sanitizado, tipo, tamanho, identificador externo, versão e timestamps sem guardar o binário no PostgreSQL.

#### Scenario: Médico anexa resultado ao atendimento
- **WHEN** o Médico responsável envia um arquivo válido durante uma Consulta autorizada
- **THEN** o sistema persiste o vínculo clínico e os metadados do ativo retornado pelo provedor

#### Scenario: Contexto clínico divergente
- **WHEN** Paciente, Consulta e Atendimento informados não representam a mesma jornada
- **THEN** o servidor rejeita a operação antes de enviar ou persistir o arquivo

### Requirement: Upload valida arquivo antes de transmitir
O sistema MUST aceitar somente formatos clínicos configurados, MUST limitar o tamanho, MUST rejeitar arquivo vazio ou nome inválido e MUST realizar a transmissão ao armazenamento pelo servidor sem expor segredo do provedor ao cliente.

#### Scenario: PDF ou imagem dentro do limite
- **WHEN** usuário autorizado envia arquivo permitido e íntegro
- **THEN** o servidor realiza o upload privado e confirma o registro somente após resposta válida do provedor

#### Scenario: Formato ou tamanho não permitido
- **WHEN** o arquivo viola tipo, extensão ou limite configurado
- **THEN** a operação falha sem transmitir o conteúdo e a UI informa a regra violada sem ecoar dados clínicos

### Requirement: Acesso ao conteúdo é autorizado por recurso
O sistema MUST autorizar cada leitura do anexo no servidor. Médico MUST acessar somente pacientes abrangidos pelo vínculo clínico permitido; Paciente MUST acessar somente anexos próprios explicitamente liberados; Recepção e Financeiro MUST NOT obter o conteúdo clínico.

#### Scenario: Paciente abre documento próprio liberado
- **WHEN** Paciente autenticado solicita anexo próprio marcado como disponível no portal
- **THEN** o servidor gera acesso temporário ao ativo privado sem revelar credenciais ou URL permanente

#### Scenario: Usuário troca o identificador do anexo
- **WHEN** uma identidade solicita anexo fora do próprio escopo
- **THEN** o servidor nega a leitura sem confirmar a existência do documento

### Requirement: Exclusão é auditável e consistente
O sistema MUST registrar quem solicitou a exclusão e MUST manter o registro em estado removido quando a exclusão externa for confirmada; falha externa MUST NOT apagar silenciosamente o vínculo local.

#### Scenario: Exclusão concluída
- **WHEN** Médico autorizado remove um anexo não bloqueado por política de retenção
- **THEN** o ativo externo é removido, o registro local é marcado como removido e a auditoria é persistida

#### Scenario: Provedor indisponível durante exclusão
- **WHEN** a remoção externa falha ou expira
- **THEN** o sistema mantém o registro recuperável, sinaliza falha operacional e permite nova tentativa idempotente

### Requirement: Integração indisponível não simula sucesso
O sistema MUST apresentar estado não configurado ou indisponível quando as credenciais do armazenamento não existirem ou o provedor falhar e MUST NOT gerar identificadores ou arquivos fictícios.

#### Scenario: Credenciais ausentes
- **WHEN** usuário autorizado tenta enviar arquivo sem configuração completa
- **THEN** o upload fica indisponível com orientação operacional segura e nenhum registro de sucesso é criado

### Requirement: Operações sensíveis são auditadas sem conteúdo clínico
O sistema MUST auditar criação, liberação, acesso e remoção usando identificadores, ator, resultado e horário, MUST NOT registrar binário, URL assinada, CPF, conteúdo ou credenciais.

#### Scenario: Download autorizado
- **WHEN** o servidor concede acesso temporário ao anexo
- **THEN** a auditoria registra ator, recurso e resultado sem incluir o endereço temporário

