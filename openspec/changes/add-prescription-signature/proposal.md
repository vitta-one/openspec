# Proposal — Assinatura demonstrativa de prescrições

## Por que

O Vitta One possui prescrição estruturada com visualização HTML para impressão, mas não possui módulo de assinatura ZapSign na `develop`. Não se pode mostrar um documento como assinado sem confirmação de provedor.

## O que muda

- Definir fluxo de envio de um snapshot imutável de Prescription elegível para assinatura demonstrativa em ZapSign Sandbox.
- Persistir referência ao documento, versão/hash, autor, estado e eventos relevantes.
- Tratar autenticação, webhooks, idempotência, falhas incertas e estado histórico sem modificar silenciosamente itens da prescrição.
- Permitir ao Médico autorizado consultar o estado verificado, preservando impressão atual.

## Capabilities

### New Capabilities

- `prescription-signature`: preparação de documento, envio Sandbox, confirmação, histórico e auditoria.

### Modified Capabilities

- `clinical-prescription`: compatibilidade de mutabilidade/imutabilidade será definida por delta após aprovação, sem alterar o contrato agora.

## Fora do escopo

Assinatura com efeitos jurídicos assegurados, produção, certificados ICP-Brasil, QR com validade legal, prontuário certificado, envio de documento para paciente por comunicação não autorizada ou assinatura por Médico alheio.

## Decisões pendentes

Momento de congelamento, forma de consentimento/autenticação do signatário, formato do arquivo de origem, política de múltiplas versões, tempo de retenção, regras de cancelamento e status de reprocessamento.

## Riscos

Webhook forjado/duplicado, resultado de envio desconhecido, reenvio gerando documentos duplicados, edição durante assinatura, exposição de CPF/documentos, link de consulta aberto, perda de disponibilidade ZapSign. Sandbox obrigatório.
