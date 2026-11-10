## Purpose

Fornecer operação financeira real e auditável para a clínica, com catálogo de serviços, contas do paciente, cobranças e conciliação em Asaas Sandbox.

## ADDED Requirements

### Requirement: Catálogo financeiro usa valores monetários exatos
O sistema MUST permitir que Financeiro administre serviços ativos com nome, descrição e preço em centavos inteiros positivos; registros já usados MUST ser inativados em vez de removidos de forma destrutiva.

#### Scenario: Serviço válido é criado
- **WHEN** Financeiro informa nome único e preço positivo
- **THEN** o serviço fica disponível para novas contas sem arredondamento binário

#### Scenario: Serviço usado é inativado
- **WHEN** Financeiro desativa serviço referenciado por uma conta
- **THEN** o histórico preserva nome e valor originais e o serviço deixa de aparecer em novas seleções

### Requirement: Conta do paciente preserva snapshot dos itens
O sistema MUST vincular cada conta a um Paciente, MUST persistir itens com descrição, quantidade, valor unitário e total calculado no servidor e MUST impedir totais negativos ou divergentes.

#### Scenario: Conta é emitida
- **WHEN** Financeiro confirma itens válidos para Paciente existente
- **THEN** o total é calculado em centavos e a conta recebe identificador e estado aberto

#### Scenario: Total enviado pelo cliente diverge
- **WHEN** a UI informa total diferente da soma server-side
- **THEN** o servidor ignora o total do cliente, rejeita a inconsistência e não emite cobrança

### Requirement: Cobrança Asaas é criada de forma idempotente
O sistema MUST criar primeiro uma intenção local única, MUST localizar ou criar o cliente externo pelo identificador interno e MUST relacionar a cobrança com `externalReference`; repetição da operação MUST NOT gerar cobrança duplicada.

#### Scenario: Cobrança Sandbox criada
- **WHEN** Financeiro solicita cobrança para conta aberta com integração configurada
- **THEN** o sistema persiste identificador externo, forma de pagamento, vencimento, URL da fatura e estado retornado

#### Scenario: Retry após timeout
- **WHEN** a resposta anterior é incerta
- **THEN** o sistema reconcilia por referência externa antes de decidir criar nova cobrança

### Requirement: Cartão não é processado pelo Vitta One
O sistema MUST NOT coletar, persistir ou transmitir número, CVV ou dados brutos de cartão; quando cartão estiver disponível, o Paciente MUST ser direcionado à superfície hospedada pelo provedor.

#### Scenario: Pagamento com cartão
- **WHEN** Paciente escolhe cartão para uma cobrança permitida
- **THEN** a aplicação abre a fatura hospedada sem receber dados do cartão

### Requirement: Webhook Asaas é autenticado, persistido e idempotente
O sistema MUST validar `asaas-access-token`, MUST persistir o id único antes de processar e MUST reconciliar cobrança e pagamento atomicamente; eventos repetidos MUST NOT duplicar pagamentos.

#### Scenario: Pagamento recebido
- **WHEN** evento autenticado `PAYMENT_RECEIVED` referencia cobrança conhecida
- **THEN** um pagamento é registrado uma vez e os saldos da conta são recalculados

#### Scenario: Evento duplicado
- **WHEN** o mesmo id de evento é entregue novamente
- **THEN** o endpoint confirma o recebimento sem duplicar valor ou auditoria de negócio

### Requirement: Dashboard deriva somente de dados persistidos
O sistema MUST calcular valores atuais em aberto, vencidos, recebidos e quantidade de contas a partir de contas e pagamentos reais; buscas e filtros de situação MUST operar somente sobre a projeção autorizada.

#### Scenario: Nenhum movimento encontrado
- **WHEN** a busca ou o filtro não encontra dados
- **THEN** o dashboard mostra estado vazio e valores zero sem métricas fictícias

#### Scenario: Pagamento conciliado
- **WHEN** um pagamento válido é persistido
- **THEN** os indicadores e a situação da conta refletem o novo saldo

### Requirement: Autorização financeira é aplicada no servidor
O sistema MUST restringir catálogo, emissão, cancelamento e conciliação à role Financeiro; Paciente MUST acessar somente as próprias contas e links; outras roles MUST receber apenas os resumos explicitamente necessários ao fluxo clínico.

#### Scenario: Paciente consulta conta própria
- **WHEN** Paciente autenticado abre a área financeira do portal
- **THEN** o servidor retorna somente contas e cobranças vinculadas ao seu cadastro

#### Scenario: Paciente troca identificador da conta
- **WHEN** Paciente solicita conta de outra pessoa
- **THEN** a leitura é negada sem revelar existência, valores ou nome do titular

### Requirement: Integração permanece Sandbox e falha de forma segura
O sistema MUST usar a URL Sandbox por padrão nesta change, MUST exigir opt-in explícito para qualquer ambiente diferente e MUST comunicar configuração ausente sem simular cobranças.

#### Scenario: Chave ausente
- **WHEN** Financeiro tenta emitir cobrança sem configuração Asaas
- **THEN** a conta local permanece intacta, nenhuma cobrança falsa é criada e a interface mostra indisponibilidade operacional

