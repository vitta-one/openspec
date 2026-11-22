## ADDED Requirements

### Requirement: Assinatura só pode começar para prescrição autorizada
O sistema MUST validar a identidade do Médico responsável, o vínculo clínico e a elegibilidade do documento antes de iniciar assinatura demonstrativa, sem criar permissão para outro papel.

#### Scenario: Médico responsável envia
- **WHEN** o Médico autorizado seleciona Prescription elegível e confirma envio
- **THEN** uma operação com referência persistida a essa prescrição é criada de forma transacional

#### Scenario: Outro Médico
- **WHEN** outro Médico tenta enviar ou consultar assinatura por identificador de Prescrição
- **THEN** o servidor rejeita e não expõe conteúdo nem link do documento

### Requirement: Conteúdo submetido é imutável durante a assinatura
O sistema MUST associar a operação ao snapshot e identificador de versão/hash da Prescrição enviada e MUST NOT aplicar alterações posteriores silenciosamente ao documento em andamento.

#### Scenario: Prescrição alterada durante assinatura
- **WHEN** surge tentativa de mudar conteúdo depois do snapshot submetido
- **THEN** a alteração é bloqueada ou requer nova versão aprovada explicitamente, preservando rastreabilidade

### Requirement: Integração ZapSign opera exclusivamente em Sandbox
O sistema MUST utilizar configurações seguras no servidor e MUST rejeitar chave/endpoint de produção enquanto o projeto estiver limitado ao Sandbox.

#### Scenario: Configuração ausente ou de produção
- **WHEN** chave ou endpoint não atende à política Sandbox
- **THEN** o envio é bloqueado sem transmitir dados clínicos

#### Scenario: Resultado de envio incerto
- **WHEN** ocorre timeout após tentativa de criar documento
- **THEN** o estado fica indeterminado e a aplicação exige conciliação em vez de repetir POST cegamente

### Requirement: Estado assinado depende de confirmação autenticada
O sistema MUST verificar a autenticidade dos eventos e reconciliar a referência externa antes de projetar assinatura concluída.

#### Scenario: Evento válido
- **WHEN** o webhook legítimo confirma a assinatura do documento elegível
- **THEN** o estado persistido avança e registra autoria e instante da transição

#### Scenario: Webhook duplicado ou fora de ordem
- **WHEN** a mesma confirmação chega novamente ou um estado antigo chega depois
- **THEN** o processamento é idempotente e não regride nem duplica assinatura

#### Scenario: Webhook forjado
- **WHEN** a autenticidade do evento não pode ser comprovada
- **THEN** a mensagem é rejeitada sem atualizar assinatura

### Requirement: Histórico distingue documento imprimível de assinado
O sistema MUST manter visualização/ impressão preexistente e MUST exibir rótulo de assinatura somente quando houver evidência do provedor, sem prometer validade jurídica.

#### Scenario: Documento não assinado
- **WHEN** não existe confirmação verificável
- **THEN** a visualização permanece como prescrição não assinada e informa o estado real

#### Scenario: Provedor indisponível
- **WHEN** consulta ao ZapSign falha temporariamente
- **THEN** a interface mantém o último status verificado, sinaliza incerteza e preserva o acesso protegido à prescrição
