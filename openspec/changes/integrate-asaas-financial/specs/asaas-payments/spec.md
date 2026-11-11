# Spec Delta — Pagamentos Asaas

## Purpose

Integrar pacientes e cobranças ao Asaas Sandbox com integridade local, autenticação de eventos, recuperação de falhas externas e conciliação verificável.

## ADDED Requirements

### Requirement: Cliente financeiro único sob demanda
O sistema MUST reutilizar o cliente Asaas vinculado ao paciente e MUST criar cliente somente ao precisar de cobrança. Nome e CPF válidos MUST ser validados antes da chamada; atualizações MUST preservar o vínculo. Resultado incerto MUST bloquear nova criação até conciliação. Dados enviados MUST ser limitados à finalidade financeira.

#### Scenario: Primeiro cliente e atualização
- **GIVEN** paciente válido ainda sem cliente financeiro
- **WHEN** operador autorizado inicia emissão
- **THEN** o sistema consulta a referência externa antes de criar, vincula um único cliente e reutiliza o vínculo nas próximas emissões; atualização válida preserva o identificador externo.

#### Scenario: Cliente duplicado no provedor
- **WHEN** a busca externa encontra mais de um cliente correspondente
- **THEN** o sistema bloqueia a vinculação ambígua para revisão, sem criar outro cliente.

#### Scenario: Concorrência e timeout de criação
- **WHEN** duas emissões do mesmo paciente competem ou o POST de cliente expira
- **THEN** o sistema mantém uma intenção por paciente e concilia a referência antes de permitir outro POST.

### Requirement: Emissão Pix e boleto com consulta posterior
O sistema MUST emitir cobrança Pix ou boleto com cliente, valor, vencimento e referência local persistida, recuperar link do provedor e obter dados Pix quando aplicável. MUST consultar estado por identificador externo e MUST NOT interpretar criação ou retorno do navegador como pagamento. Cartão MUST permanecer indisponível até homologação de fluxo hospedado ou tokenizado.

#### Scenario: Pix emitido
- **WHEN** a emissão autorizada recebe resposta válida do Sandbox
- **THEN** persiste identificador e estado reais, disponibiliza link e dados Pix obtidos do provedor, sem registrar pagamento recebido.

#### Scenario: Boleto emitido
- **WHEN** cobrança BOLETO recebe resposta válida
- **THEN** disponibiliza o link retornado e mantém a cobrança aguardando confirmação externa.

#### Scenario: Link inválido ou cartão não homologado
- **WHEN** o provedor retorna URL insegura/inesperada ou a emissão pede cartão
- **THEN** nenhum link inseguro é apresentado e cartão é recusado antes de coletar dados sensíveis.

### Requirement: Falhas externas não geram repetição cega
O sistema MUST distinguir rejeição confirmada de resultado desconhecido. Timeout, resposta inválida ou falha após envio MUST deixar intenção recuperável e impedir novo POST até consulta externa. Leituras temporariamente indisponíveis MUST preservar os dados locais e indicar necessidade de conciliação. Configuração ausente ou ambiente de produção MUST bloquear operações externas.

#### Scenario: Timeout ao criar cobrança
- **WHEN** a API expira após possível criação
- **THEN** a intenção fica UNKNOWN, não libera segunda emissão e a conciliação busca a referência persistida antes de qualquer nova tentativa autorizada.

#### Scenario: Limite ou rede indisponível
- **WHEN** consulta recebe 429, 5xx ou erro de rede
- **THEN** a falha é registrada sem segredos, respeita Retry-After em nova leitura e não marca cobrança como paga ou inexistente.

#### Scenario: Configuração ausente e cobrança não encontrada
- **WHEN** falta chave/base Sandbox ou uma consulta externa retorna 404
- **THEN** respectivamente bloqueia a chamada ou registra divergência recuperável; nenhum pagamento local é apagado.

### Requirement: Webhook autenticado e durável
O sistema MUST validar `asaas-access-token` antes de aceitar evento, exigir identificador de evento e pagamento, limitar o corpo a 256 KiB e persistir uma única ocorrência por evento. MUST responder HTTP 200 somente após persistência, inclusive para duplicado já persistido; falha de banco MUST permitir redelivery. O recebimento MUST NOT aguardar envio de e-mail.

#### Scenario: Webhook legítimo
- **WHEN** evento válido chega com token configurado correto
- **THEN** persiste evento mínimo e responde 200 para processamento separado.

#### Scenario: Webhook sem autenticação
- **WHEN** token falta, diverge ou a configuração está ausente
- **THEN** responde 401 ou 503 sem persistir efeito financeiro.

#### Scenario: Webhook duplicado
- **GIVEN** evento já persistido/processado
- **WHEN** o mesmo id chega novamente, inclusive simultaneamente
- **THEN** responde 200 sem repetir transição, cobrança ou notificação.

#### Scenario: Payload inválido ou banco indisponível
- **WHEN** faltam campos, o corpo excede o limite ou não é possível persistir
- **THEN** responde respectivamente 400, 413 ou 503, sem sinalizar sucesso falso.

### Requirement: Estado externo conciliado preserva ciclo clínico
O sistema MUST reconciliar pagamento pelo Asaas antes de aplicar evento, conferir cliente, referência, moeda implícita BRL e valor esperado e preservar estado externo e interno. Estado desconhecido MUST exigir revisão. Evento e transição MUST ser registrados na mesma transação; falha temporária MUST manter evento pendente. Ciclo clínico MUST permanecer independente.

#### Scenario: Pagamento Pix confirmado
- **GIVEN** cobrança Pix pendente associada a Consulta
- **WHEN** evento autenticado PAYMENT_RECEIVED é reconciliado com estado RECEIVED e dados correspondentes
- **THEN** atualiza pagamento para RECEIVED, registra evento idempotente e intenção de comunicação
- **AND** não marca a Consulta como concluída.

#### Scenario: Evento fora de ordem
- **GIVEN** pagamento recebido e evento anterior de atraso chega depois
- **WHEN** o evento é processado
- **THEN** usa o estado atual consultado na API, sem regredir para vencido apenas pela ordem de chegada.

#### Scenario: Cobrança externa desconhecida ou divergente
- **WHEN** evento referencia cobrança sem vínculo ou valores/cliente divergentes
- **THEN** coloca evento em revisão sem criar cobrança clínica nem alterar valores aceitos.

#### Scenario: Confirmação sem disponibilização
- **WHEN** PAYMENT_CONFIRMED é conciliado como CONFIRMED
- **THEN** apresenta confirmação aguardando disponibilização, sem somar ao recebido nem enviar confirmação de valor recebido.

### Requirement: Cancelamento e estorno suportados
O sistema MUST permitir cancelamento somente de cobrança pendente/vencida após releitura externa e confirmação autorizada. MUST permitir estorno integral Pix recebido somente ao Administrador, com motivo, quando suportado. Operação incerta MUST bloquear repetição e exigir conciliação; estorno solicitado MUST NOT ser exibido como concluído antes da confirmação externa.

#### Scenario: Cancelamento válido
- **WHEN** operador autorizado confirma cancelamento de cobrança ainda pendente na API
- **THEN** solicita exclusão externa, concilia e registra histórico sem cancelar Consulta.

#### Scenario: Pagamento chegou antes do cancelamento
- **WHEN** a consulta externa indica recebimento antes da operação
- **THEN** recusa cancelamento e oferece somente o fluxo de estorno autorizado aplicável.

#### Scenario: Estorno e saldo insuficiente
- **WHEN** Administrador confirma estorno integral Pix e a API aceita ou rejeita por saldo
- **THEN** registra respectivamente solicitação/conciliação ou rejeição, sem falsificar REFUNDED nem repetir POST.

#### Scenario: Estorno de boleto
- **WHEN** é solicitado estorno de boleto pelo fluxo desta versão
- **THEN** a operação é recusada com explicação de método não homologado, preservando histórico.
