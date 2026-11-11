# Proposal — Financeiro Asaas Sandbox

## Why

As rotas financeiras existem, mas não há entidades, serviços ou integração de pagamentos no código auditado da `develop` (`156b0a6`). A clínica precisa emitir e acompanhar cobranças vinculadas às Consultas sem interferir no atendimento clínico.

## What Changes

- Objetivo: entregar financeiro básico a médio com Pix e boleto no Asaas Sandbox, persistência, conciliação e histórico.
- Vincular paciente a cliente Asaas sob demanda e impedir duplicidades locais e após resultados externos incertos.
- Emitir, consultar e cancelar cobranças autorizadas; estorno integral de Pix recebido restrito ao Administrador e ao suporte da conta.
- Receber webhooks autenticados em inbox persistente, processar assincronamente e reconciliar com a API.
- Substituir o shell `/financeiro` por indicadores, evolução por período, pesquisa, filtros, paginação, detalhes, Pix e boleto reais.
- Tornar `/admin/financeiro` área administrativa normal com operações autorizadas, sem flag QA; preservar guards das demais prévias.
- Registrar eventos financeiros elegíveis para a change independente de Resend; não chamar e-mail no recebimento de webhook.

## Capabilities

### New Capabilities

- `financial-management`: autorização, projeções persistidas, indicadores e gestão financeira.
- `asaas-payments`: clientes, cobranças, cancelamento, estorno suportado, inbox e conciliação.
- `payment-notifications`: contrato de eventos financeiros para comunicação desacoplada.

### Modified Capabilities

Nenhuma: as regras clínicas e de autenticação existentes são preservadas. A nova capability define suas próprias operações autorizadas, sem conceder acesso à Recepção clínica.

## Impact

- Reutilizar `Patient`, `Consultation`, sessões/RBAC, SQLModel, Alembic, `httpx`, shell e tokens visuais.
- Adicionar módulo `vitta_one/financial/`, modelos financeiros, migrations aditivas, handlers no servidor Reflex e testes.
- Pontos compartilhados: `vitta_one/vitta_one.py`, `ui/pages.py`, auth/roteamento e preview administrativo. Não alterar outras prévias QA.
- Dependências: PostgreSQL isolado, configuração Sandbox e URL HTTPS temporária para webhooks; a comunicação depende de `extend-resend-email`, mas emissão e consulta não dependem do Resend.

## Fora do escopo

Produção, cartão sem homologação, parcelas, assinaturas, split, NF-e, contabilidade, juros/multas configurados pela aplicação, pagamentos de walk-in sem Consulta e recibos sem documento válido. Não coletar PAN/CVV. Nenhuma nova role.

## Riscos técnicos e de segurança

- Asaas permite clientes duplicados; `externalReference` não é uma constraint de unicidade externa. Timeout exige conciliação antes de repetir POST.
- Sem transação distribuída entre PostgreSQL e Asaas: persistir intenção e resultado desconhecido, com recuperação operacional.
- Eventos podem chegar repetidos/fora de ordem; reconciliar sem regressão baseada apenas na ordem de chegada.
- Credenciais e dados pessoais exclusivamente no backend; logs sem corpo HTTP, CPF, tokens ou links completos.
- Banco possui cabeça Alembic `e9d3a8c2b170`; encadear migrations sem editar as existentes e revalidar após atualizações da base.

## Estratégia de testes

Contratos httpx mockados, autorização por todas as roles, integridade/concorrência em PostgreSQL, falhas externas e recuperação, compilação Reflex, E2E desktop/mobile e execução controlada no Sandbox. Evidências devem separar mock, Sandbox real e produção (fora do escopo).

## Critérios de conclusão

Requisitos correspondem ao código; tasks verificadas; Pix/boleto e webhook exercitados no Sandbox; indicadores vêm do banco; acesso negado testado; regressões relevantes passam; migrations validadas; OpenSpec strict válido; arquivamento somente após evidências completas.

## Decisões aprovadas em 11/11/2026

O usuário aprovou: Administrador e Financeiro emitem/cancelam; somente Administrador solicita estorno integral; Recepcionista e Médico sem acesso financeiro. Acesso interno do Paciente não é ampliado. Uma cobrança não cancelada/não estornada por Consulta, com valor em BRL informado pelo operador autorizado. `/admin/financeiro` passa a área administrativa normal. Cancelar Consulta não cancela cobrança automaticamente, preservando a independência exigida na missão. Cartão fica pendente de homologação; estorno implementado inicialmente somente para Pix suportado.
