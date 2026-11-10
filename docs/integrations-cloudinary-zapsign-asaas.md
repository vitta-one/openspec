# Integrações clínicas e financeiras

Este guia cobre os adapters de Cloudinary, ZapSign e Asaas implementados no Vitta One. As credenciais existem somente no ambiente do servidor. O navegador nunca recebe API keys, tokens de webhook ou segredos de assinatura.

## Comportamento sem credenciais

O sistema continua inicializando sem as três integrações. As telas exibem estado indisponível e as operações externas falham com mensagem segura, sem simular sucesso. Configuração parcial é tratada como inválida. Consulte [`.env.example`](../.env.example) para os nomes das variáveis.

## Cloudinary — anexos clínicos

- upload autenticado e assinado no servidor;
- formatos aceitos: PDF, JPEG e PNG;
- limite padrão: 10 MiB, configurável por `VITTA_ONE_ATTACHMENT_MAX_BYTES`;
- ativo privado por padrão e liberação explícita para o portal do paciente;
- link de download assinado e temporário (300 segundos por padrão);
- exclusão no provedor antes da marcação local como removido;
- auditoria de upload, liberação, revogação, download e exclusão.

Defina `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY` e `CLOUDINARY_API_SECRET`. Se uma das três estiver ausente, a configuração é rejeitada.

## ZapSign — assinatura da prescrição

Defina `ZAPSIGN_API_TOKEN` e um segredo aleatório próprio em `ZAPSIGN_WEBHOOK_TOKEN`. Configure o endpoint abaixo no provedor, incluindo o header `Authorization: Bearer <ZAPSIGN_WEBHOOK_TOKEN>`:

```text
POST https://SEU_DOMINIO/api/webhooks/zapsign
Content-Type: application/json
```

A primeira solicitação cria uma identidade idempotente por prescrição e bloqueia sua edição. Repetir a ação não cria outro registro local. O webhook é deduplicado, estados finais não retrocedem e o PDF final é consultado no provedor somente após `SIGNED`. Se o resultado da criação for incerto, a solicitação fica em `RECONCILIATION_REQUIRED`; o sistema não repete automaticamente uma escrita que poderia duplicar o documento.

## Asaas Sandbox — contas e cobranças

O ambiente padrão é `https://api-sandbox.asaas.com/v3`. Defina `ASAAS_API_KEY` e `ASAAS_WEBHOOK_TOKEN`. Configure o endpoint no Sandbox com o token de autenticação do webhook:

```text
POST https://SEU_DOMINIO/api/webhooks/asaas
Content-Type: application/json
asaas-access-token: <ASAAS_WEBHOOK_TOKEN>
```

Valores são persistidos em centavos. A conta guarda uma cópia do nome e preço dos serviços emitidos. Clientes e cobranças usam referências externas estáveis. Em timeout de criação, a cobrança fica em `RECONCILIATION_REQUIRED`; a ação **Verificar no Asaas** consulta a referência externa e nunca cria outra cobrança. Eventos repetidos não duplicam pagamentos.

Produção é bloqueada por padrão. Para usar `https://api.asaas.com/v3`, é obrigatório também definir `VITTA_ONE_ALLOW_ASAAS_PRODUCTION=true` após revisão operacional explícita.

## Segurança dos webhooks

- somente `application/json`;
- body máximo de 256 KiB;
- comparação constante do token;
- respostas com `Cache-Control: no-store`;
- mensagens sem payload, segredo ou dado clínico;
- persistência do identificador do evento para deduplicação.

## Diagnóstico

1. Confirme que todas as variáveis do mesmo provedor foram definidas.
2. Verifique o status mostrado na interface; `NOT_CONFIGURED` e `INVALID_CONFIGURATION` não significam sucesso.
3. Use apenas dados sintéticos no Sandbox.
4. Consulte os registros de auditoria e os códigos de estado, sem registrar o conteúdo clínico ou tokens.
5. Não reenvie manualmente uma operação marcada como resultado incerto; use a reconciliação prevista.

## Validação recomendada

Execute em PostgreSQL QA isolado:

```bash
alembic upgrade head
pytest -q
reflex compile --dry
```

Depois valide upload/download, assinatura e cobrança com contas Sandbox próprias. Nunca execute migrations ou webhooks sintéticos em produção durante a homologação.
