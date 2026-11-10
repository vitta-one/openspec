## Purpose

Controlar a assinatura digital de prescrições no ZapSign com estados locais confiáveis, processamento idempotente e acesso protegido ao documento final.

## ADDED Requirements

### Requirement: Somente Prescrição válida pode ser enviada para assinatura
O sistema MUST permitir que somente o Médico autor envie uma Prescrição persistida, completa e ainda não enviada; MUST validar o contexto clínico e o e-mail do signatário antes de transmitir o documento.

#### Scenario: Envio autorizado
- **WHEN** o Médico autor confirma o envio de uma Prescrição completa
- **THEN** o servidor cria uma solicitação local idempotente, envia o documento e persiste os identificadores externos retornados

#### Scenario: Repetição da mesma ação
- **WHEN** a ação de envio é repetida para a mesma Prescrição
- **THEN** o sistema retorna a solicitação existente sem criar documento duplicado no provedor

### Requirement: Estado local representa o ciclo externo
O sistema MUST manter estados explícitos para não enviada, envio em processamento, aguardando assinatura, assinada, recusada, expirada, cancelada e falha, com timestamps e motivo operacional sanitizado.

#### Scenario: Documento aceito pelo provedor
- **WHEN** o provedor confirma a criação
- **THEN** a solicitação local passa a aguardando assinatura e guarda somente identificadores necessários à reconciliação

#### Scenario: Timeout após resultado incerto
- **WHEN** a chamada expira sem confirmação segura
- **THEN** o estado fica marcado para reconciliação e novas tentativas não criam outro documento sem confirmação por webhook ou operação assistida no provedor

### Requirement: Webhook é autenticado e idempotente
O sistema MUST validar o segredo configurado para o endpoint, MUST rejeitar payload inválido, MUST persistir um identificador único do evento e MUST processar entregas repetidas no máximo uma vez.

#### Scenario: Evento assinado recebido pela primeira vez
- **WHEN** um webhook autenticado informa estado final para documento conhecido
- **THEN** o evento é registrado e a solicitação local é atualizada atomicamente

#### Scenario: Reentrega do mesmo evento
- **WHEN** o mesmo identificador de evento é entregue novamente
- **THEN** o endpoint responde com sucesso sem repetir efeitos

#### Scenario: Token de webhook inválido
- **WHEN** a autenticação do webhook não corresponde à configuração
- **THEN** o servidor rejeita a requisição sem alterar estados ou revelar recursos

### Requirement: Documento assinado é obtido de forma protegida
O sistema MUST permitir que o Médico autor e o Paciente titular obtenham o documento assinado; MUST consultar o provedor quando necessário e MUST NOT tratar URL temporária como endereço permanente.

#### Scenario: Documento já assinado
- **WHEN** usuário autorizado solicita a versão assinada
- **THEN** o servidor obtém uma referência válida atual e concede acesso sem expor token de API

#### Scenario: Documento ainda pendente
- **WHEN** usuário solicita a versão final antes da assinatura
- **THEN** a interface informa o estado atual e não apresenta documento fictício

### Requirement: Prescrição enviada torna-se imutável
O sistema MUST impedir alteração ou exclusão do conteúdo de uma Prescrição a partir do primeiro envio para assinatura, independentemente do estado posterior da solicitação.

#### Scenario: Médico tenta editar depois do envio
- **WHEN** existe solicitação de assinatura para a Prescrição
- **THEN** o servidor rejeita a mutação e preserva exatamente o conteúdo enviado

### Requirement: Ausência de credenciais mantém modo honesto
O sistema MUST manter a Prescrição clínica e sua impressão local utilizáveis quando o ZapSign não estiver configurado, mas MUST desabilitar o envio e comunicar que a assinatura digital está indisponível.

#### Scenario: Integração não configurada
- **WHEN** Médico abre uma Prescrição sem credenciais completas
- **THEN** o conteúdo permanece legível e imprimível, o envio não é executado e nenhum selo de assinatura é mostrado

