# Design — Assinatura ZapSign (proposta não implementada)

## Arquitetura

A integração se adiciona ao monólito Reflex existente: State/UI → serviço de assinatura → snapshot imutável de Prescription → adaptador ZapSign Sandbox → estado persistido. Webhook autenticado ingressa no backend Reflex e é processado de modo idempotente.

## Persistência prevista

Registro de documento por versão/hash e Prescription; operação de envio com estado durável; eventos de webhook deduplicados e trilha de transições. A estrutura exata depende de revisão de models e política de versões; migrations somente aditivas.

## Invariantes

- Médico só inicia/consulta assinatura de prescrição para episódio autorizado.
- Conteúdo enviado e hash permanecem imutáveis após iniciar processo.
- O status `ASSINADO` é exibido apenas após confirmação verificável, não após resposta HTTP de criação.
- Resposta incerta não provoca repetição automática de envio; exige reconciliação.
- Webhooks são autenticados, limitados, deduplicados e resistentes a eventos fora de ordem.
- Impressão HTML atual continua disponível independentemente do provedor.

## Review obrigatório

Definir autenticação do signatário, snapshot/formato, versão, estados exatos suportados pelo provedor, política de links e retenção, restrições do sandbox e critérios de homologação.
