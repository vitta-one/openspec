## Context

Veja `proposal.md` para motivação. A `develop` já possui autenticação/RBAC, vínculo `Patient.user_id`, agenda, consulta, prontuário, prescrições estruturadas, portal do paciente e um transformer Starlette montado no ASGI do Reflex. Exames, assinatura e financeiro não possuem modelos nem serviços. `httpx` já faz parte das dependências; não é necessário adicionar SDKs de fornecedores.

As integrações devem operar sem credenciais no desenvolvimento, nunca produzir sucesso simulado e manter segredos fora de banco, logs e frontend. Webhooks chegam fora de uma sessão Reflex e precisam de autenticação própria, idempotência e transações curtas.

## Goals / Non-Goals

**Goals:**

- Manter domínio, persistência e autorização independentes dos clientes HTTP externos.
- Preservar uma fonte de verdade local reconciliável, inclusive após timeout e reentrega.
- Usar PostgreSQL para integridade, locking e idempotência, com migrations explícitas.
- Entregar superfícies Reflex coerentes com o design system e com estados degradados honestos.
- Permitir testes determinísticos com transports HTTP falsos, sem chamar Sandbox no Pytest comum.

**Non-Goals:**

- Integração com laboratórios, OCR ou interpretação automática de exames.
- Certificação jurídica própria, assinatura fora do ZapSign ou armazenamento permanente de URL temporária.
- Processamento de dados de cartão, conta bancária, split ou produção Asaas.
- Job queue distribuída. Reprocessamento é síncrono e explícito nesta etapa; webhooks persistem antes de aplicar efeitos.
- Alterar o framework Reflex ou introduzir uma API REST paralela para fluxos de UI.

## Decisions

### 1. Módulos verticais e portas HTTP pequenas

Serão criados `clinical_documents`, `digital_signature` e `finance`, cada um com `settings.py`, `client.py`, `service.py`, `application.py`/`state.py` quando necessário, modelos próprios e erros sanitizados. O cliente recebe `httpx.Client`/transport opcional para testes, usa timeout total curto e nunca conhece sessão ou role.

Alternativa considerada: SDKs oficiais de cada fornecedor. Foi rejeitada para evitar três dependências, configuração global e superfícies maiores de atualização; os contratos usados são pequenos e documentados.

### 2. Upload privado realizado pelo servidor

Arquivos são validados antes do envio e transmitidos do backend à Upload API do Cloudinary com assinatura SHA-256 gerada no servidor. O registro armazena `asset_id`, `public_id`, `version`, `resource_type`, `format` e tamanho; download usa URL temporária assinada. O segredo nunca chega ao navegador.

Alternativa considerada: upload unsigned direto. Foi rejeitada porque o conteúdo é clínico e exige escopo, validação e auditoria server-side antes da transmissão.

### 3. Estado local antes de efeito externo

Envio de assinatura e emissão de cobrança criam uma operação local com `request_key` único antes da chamada. Em timeout, a operação fica em estado de resultado incerto. A cobrança pode ser reconciliada por `externalReference`; a assinatura permanece bloqueada para confirmação por webhook ou operação assistida, pois a API de listagem não oferece filtro confiável por `external_id`. Nenhuma das duas repete a escrita externa às cegas. Constraints únicas protegem contra duplo clique e concorrência.

Alternativa considerada: chamar o provedor e persistir depois. Foi rejeitada porque uma falha de banco após sucesso externo produziria órfãos e duplicações.

### 4. Webhooks no transformer ASGI existente

O `api_transformer` atual será ampliado com rotas Starlette para ZapSign e Asaas. Cada rota limita body, exige JSON, valida token com comparação constante, persiste um evento único e aplica transição permitida em uma única transação. A resposta não contém dados clínicos/financeiros.

Cloudinary não precisa de webhook para upload síncrono desta change. Se notificações forem habilitadas no futuro, usarão a assinatura oficial do provedor e uma change própria.

### 5. Estados explícitos, sem inferência pela UI

`PrescriptionSignatureRequest`, `PatientAccount`, `BillingCharge` e `PaymentRecord` mantêm estados enumerados por string com CheckConstraint. A UI recebe projeções prontas; não deduz “pago” por presença de URL nem “assinado” por texto. Transições externas desconhecidas são registradas como evento ignorado e não sobrescrevem estado válido.

### 6. Valores em centavos e snapshot financeiro

Todo valor é inteiro em centavos. Itens de conta guardam descrição e preço do momento, mesmo que o catálogo mude. O saldo é calculado no servidor a partir de itens e pagamentos válidos. A integração converte centavos para string decimal somente no limite HTTP.

Alternativa considerada: `float`. Foi rejeitada por arredondamento e inconsistência de totais.

### 7. Autorização por recurso em application services

Estados Reflex passam somente token e ids para funções de aplicação. Essas funções revalidam sessão, role, `Patient.user_id`, autoria Médica e vínculos de Consulta/Atendimento antes de consultar conteúdo. Clientes externos nunca recebem decisão de autorização.

### 8. Documento ZapSign gerado a partir da projeção persistida

A integração envia texto Markdown produzido a partir da mesma projeção read-only usada pela impressão, com `external_id` estável; o ZapSign gera o documento assinável. Após o primeiro envio, qualquer mutação da Prescrição é bloqueada. O webhook `doc_signed` só marca final quando o status do documento indicar conclusão; links `original_file` e `signed_file` não são persistidos como permanentes porque expiram.

### 9. Migração aditiva e rollback conservador

As tabelas são novas e a coluna/constraint de prescrição é evitada: a existência de `PrescriptionSignatureRequest` é o lock imutável. Isso reduz o impacto sobre dados existentes. O downgrade remove apenas tabelas novas em ordem de dependência; produção exige backup e janela explícita, fora desta PR.

## Risks / Trade-offs

- [Timeout após sucesso externo] → request key/external reference estável, estado `RECONCILIATION_REQUIRED`, consulta segura da cobrança e ausência de retry cego para assinatura.
- [Webhook forjado] → token dedicado por integração, comparação constante, limite de body e ausência de segredos em query string.
- [URL assinada compartilhada] → validade curta, geração somente após autorização e política `no-store` nas respostas.
- [Arquivo malicioso com MIME falso] → allowlist de extensão e MIME, limite de bytes e entrega como ativo privado; antivírus gerenciado fica fora do escopo e deve ser avaliado antes de produção clínica.
- [Eventos fora de ordem] → tabela de eventos e matriz de transição monotônica; estado final não regride por evento antigo.
- [Sem worker assíncrono] → endpoints persistem e processam operação curta; integrações lentas usam timeout e retry manual. Volume alto exigirá fila em change futura.
- [Sandbox diverge de produção] → base URL configurável com default Sandbox e bloqueio de produção sem flag explícita; homologação externa é evidência separada dos testes locais.
- [Dados clínicos em terceiros] → pasta/identificadores não incluem nome/CPF e documentação exige contrato e configuração de privacidade antes de produção.

## Migration Plan

1. Aplicar migration em PostgreSQL QA isolado e executar `upgrade head`/`downgrade -1`/`upgrade head`.
2. Implantar código sem credenciais: módulos aparecem como não configurados e não criam efeitos externos.
3. Configurar Cloudinary privado e validar upload/download/exclusão com arquivo sintético.
4. Configurar ZapSign Sandbox, endpoint autenticado e validar criação, reentrega e assinatura sintética.
5. Configurar Asaas Sandbox, webhook com token dedicado e validar cliente/cobrança/pagamento sintéticos.
6. Habilitar cada integração separadamente e acompanhar eventos/erros sanitizados.

Rollback de código mantém tabelas aditivas sem perda. Downgrade de schema só deve ocorrer em QA descartável ou após backup e decisão operacional explícita.

## Open Questions

- Antivírus/antimalware para anexos antes do uso com documentos reais.
- Política legal de retenção e exclusão de anexos e documentos assinados.
- URL pública definitiva e estratégia de worker/fila para volume de produção.
