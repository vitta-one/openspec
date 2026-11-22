# Spec Delta — Comunicação financeira

## Purpose

Publicar intenções de comunicação de cobranças e recebimentos confirmados sem acoplar o recebimento de webhooks ao provedor de e-mail.

## ADDED Requirements

### Requirement: Evento financeiro comunicado após persistência
O sistema MUST registrar evento de cobrança disponível somente após identificador e link válidos persistidos, e de pagamento confirmado somente na primeira transição conciliada para RECEIVED. Intenção de comunicação MUST compartilhar a transação do evento financeiro, com identidade estável. Falha do Resend MUST NOT desfazer pagamento confirmado.

#### Scenario: Cobrança disponível
- **GIVEN** emissão autorizada aceita e link validado
- **WHEN** o resultado é persistido
- **THEN** registra uma intenção identificada pelo evento local para consumo desacoplado.

#### Scenario: Commit financeiro falha
- **WHEN** a transação é revertida antes do commit
- **THEN** não há notificação elegível nem envio ao destinatário.

#### Scenario: Falha do Resend
- **GIVEN** pagamento recebido persistido
- **WHEN** o consumidor não consegue enviar e-mail
- **THEN** o pagamento permanece recebido e a comunicação registra seu próprio resultado.

### Requirement: Elegibilidade e frequência de comunicação financeira
Novas mensagens MUST exigir autorização de comunicação financeira ativa e endereço validado do paciente, reavaliados no momento de envio. MUST haver no máximo uma comunicação por evento e destinatário elegível. Cobrança disponível e recebimento MUST ser os únicos gatilhos financeiros iniciais; aviso de vencimento MUST permanecer desativado até regra aprovada.

#### Scenario: Paciente sem autorização
- **WHEN** evento financeiro ocorre sem preferência ativa ou sem contato elegível
- **THEN** o evento permanece auditável, mas nenhuma mensagem externa é enviada.

#### Scenario: Evento recebido novamente
- **WHEN** webhook duplicado ou conciliação repetida observa o mesmo recebimento
- **THEN** não cria nova intenção nem reenvia a confirmação.

#### Scenario: Consentimento revogado após enfileirar
- **WHEN** paciente revoga autorização antes do processamento da mensagem
- **THEN** o envio é suprimido e o motivo seguro é registrado.

### Requirement: Informação financeira mínima e verdadeira
Mensagens MUST conter somente identificação mínima, valor, vencimento e link válido quando pertinentes, sem diagnósticos, prontuário, CPF completo ou dados de cartão. Comprovante/recibo MUST NOT ser anunciado nem anexado sem documento real e válido. CONFIRMED MUST NOT ser descrito como valor recebido.

#### Scenario: Confirmação de recebimento
- **WHEN** mensagem de RECEIVED é gerada
- **THEN** identifica o pagamento e valor, sem inventar recibo fiscal ou expor conteúdo clínico.

#### Scenario: Redirecionamento do navegador
- **WHEN** navegador informa pagamento concluído sem conciliação no servidor
- **THEN** não gera mensagem de pagamento recebido nem altera a cobrança.
