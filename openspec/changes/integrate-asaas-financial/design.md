# Design — Asaas Sandbox

## Context

Ver `proposal.md` e `docs/auditoria-asaas-resend-2026-11-11.md`. Não existe persistência financeira na base auditada. Reflex já recebe API Starlette pelo `api_transformer`; httpx e SQLModel já são dependências. Serviços de agenda têm commit próprio, que deve continuar atômico com sua eventual comunicação.

## Goals / Non-Goals

**Goals:** consistência financeira local, recuperação de resultado incerto, separação do ciclo clínico e autorização em cada entrada. **Non-Goals:** transação distribuída, infraestrutura de fila externa, contabilidade ou estorno de métodos não homologados.

## Decisions

### 1. Módulo e contratos

`financial/asaas.py`: adaptador HTTP tipado para clientes, cobranças e Pix; configuração carregada apenas no backend, URL fixa/validada de Sandbox, redirects desativados, timeout connect 3s/read 10s/write 10s/pool 3s. Header `access_token`, User-Agent `Vitta-One/1.0`. Erros de domínio separados: configuração, rejeição, indisponibilidade e resultado incerto, sem propagar corpo da API ao usuário/log.

`financial/service.py`: transações e regras; `application.py`: sessão/roles, entrada validada e projeções mínimas; `state.py`: eventos Reflex, resultados serializáveis e limpeza após negar autorização; `components.py`: tabela/cards, filtros, detalhe e formulário compartilhados pelas duas rotas. Alternativa de colocar tudo no State rejeitada por misturar transporte, permissões e transações.

### 2. Persistência e integridade

| Entidade proposta | Conteúdo mínimo | Restrições |
|---|---|---|
| FinancialCustomer | paciente, id Asaas, referência local, estado de sincronização | paciente UNIQUE; id externo UNIQUE; FK RESTRICT |
| FinancialCharge | Consulta, cliente, referência UUID, id Asaas, Decimal(12,2), BRL, método, vencimento, estado externo/interno, links validados, timestamps | referência/id externo UNIQUE; CHECK valor > 0; índice único parcial por Consulta enquanto não cancelada/estornada |
| FinancialChange | cobrança, estado anterior/novo, origem, operador opcional, data, identidade estável de evento | FK RESTRICT; chave de evento UNIQUE quando aplicável |
| FinancialWebhookEvent | id evento, tipo, payment id, recebido, estado de processamento, tentativas, próxima execução, erro seguro | id evento UNIQUE; índice pendentes; não guardar corpo integral |

Não copiar nome, CPF ou prontuário para tabelas financeiras. Patient deriva da Consulta, sem FK de paciente redundante na cobrança. Guardar apenas links indispensáveis, nunca cabeçalhos ou segredos. Montantes em Decimal; converter JSON monetário sem cálculos binários e validar resposta contra valor local. Eventos de comunicação usam histórico financeiro como outbox de domínio; a change Resend cria sua intenção na mesma transação da transição quando presente. Se Resend ainda não integrado, consumidor usa identidade única do histórico para backfill controlado de eventos elegíveis, sem liberar disparos antigos automaticamente.

### 3. Emissão e falhas entre sistemas

1. Autorizar e validar Consulta, estado, valor, vencimento e método.
2. Bloquear paciente/Consulta, criar intenção com referência única e commit antes de chamada mutante; intentos existentes impedem concorrência mesmo após reinício.
3. Consultar cliente existente por vínculo/referência; se ambíguo, revisão. Criar somente sem resultado prévio e sem tentativa incerta.
4. POST de cobrança uma vez; salvar identificador e resposta validada. Resposta incerta deixa UNKNOWN e bloqueia segundo POST.
5. Conciliação explícita consulta a referência local externa com paginação; zero após timeout não autoriza repetir imediatamente: manter revisão operacional, pois não há garantia de ausência externa.

Não afirmar que `externalReference` é chave de idempotência da API. Não assumir header de idempotência Asaas sem contrato homologado. GETs podem ser retomados com backoff limitado e Retry-After; POST/DELETE não têm retry automático. Cancelamento e estorno usam intenção persistida e releitura do pagamento antes da chamada; repetição bloqueada enquanto incerta. Alternativa de manter lock de banco durante todo HTTP foi rejeitada para não sustentar transações longas.

### 4. Inbox e conciliação

POST proposto `/api/webhooks/asaas` integrado à API Reflex existente. Comparação constante do token separado de 32–255 caracteres, body máximo 256 KiB, schema mínimo. Inserção com UNIQUE; 200 depois de commit inclusive duplicados, 401 token inválido, 503 sem configuração/banco, 400 malformado e 413 excedente. Nenhum envio Resend nesse caminho.

Worker Python explícito, executado por comando/scheduler controlado, busca pendentes com `FOR UPDATE SKIP LOCKED` e lease persistido. Chamada GET externa fora do lock; aplicação com lock/revisão da cobrança impede snapshot concorrente obsoleto. Registrar estado e consumo do evento atomicamente; erro de rede mantém pendente com backoff máximo 15 min e revisão após 10 falhas. Um único consumidor por cobrança evita inversão entre snapshots; lease expirado retorna evento a pendente apenas para GET/processamento local idempotente. Eventos de outra cobrança ficam em revisão, não viram Consulta nova.

### 5. Mapeamento explícito

Estado observado na API é fonte para conciliação; evento indica o motivo de verificar, não substitui snapshot atual.

| Evento Asaas | Estado externo esperado | Estado interno | Efeito |
|---|---|---|---|
| PAYMENT_CREATED / PAYMENT_UPDATED / PAYMENT_RESTORED | PENDING (ou estado atual retornado) | PENDING | atualizar somente snapshot validado |
| PAYMENT_CONFIRMED | CONFIRMED | CONFIRMED | separar do recebido |
| PAYMENT_RECEIVED | RECEIVED | RECEIVED | histórico e comunicação uma vez |
| PAYMENT_OVERDUE | OVERDUE | OVERDUE | vencido; sem e-mail automático inicial |
| PAYMENT_DELETED | deleted=true | CANCELLED | preservar histórico |
| PAYMENT_REFUND_IN_PROGRESS | REFUND_IN_PROGRESS | REFUND_PENDING | não liberar reemissão |
| PAYMENT_REFUNDED | REFUNDED | REFUNDED | excluir dos recebidos e liberar emissão futura autorizada |
| PAYMENT_PARTIALLY_REFUNDED | parcialmente estornado | REVIEW | não permitir novo estorno/autoemissão nesta versão |
| PAYMENT_REFUND_DENIED | estado atual retornado | estado atual + histórico de recusa | não inventar estorno |
| Demais / desconhecido | desconhecido | REVIEW | suspender automação e exigir conciliação |

Pix recebido não finaliza Consulta. Cancelamento de Consulta não muta pagamento. Estado de emissão UNKNOWN não conta como recebido/pendente monetário confirmado; aparece como pendência operacional.

### 6. Projeção e UI

Filtro de período explícito: recebidos por `received_at`; pendentes/vencidos por `due_date`; listagem por vencimento, com legenda. Quantidade corresponde às cobranças do filtro da lista, incluindo encerradas; resumo deve indicar seu recorte distinto. Resumo agregado SQL; evolução diária agrupada no fuso configurado; paginação SQL 20 itens com ordenação estável. Detalhe exibe histórico real. Sem gráficos ou totais de demonstração.

Financeiro opera `/financeiro`; Administrador opera `/admin/financeiro`, sem flag de QA conforme aprovação em 11/11/2026. Demais previews conservam seus guards. Revalidar sessão e role, incluindo must_change_password, em cada operação. Confirmação contextual para cancelar/estornar com motivo; nenhuma role vem do navegador.

## Risks / Trade-offs

- [Asaas aceitou mas banco falhou] → intenção durável, UNKNOWN e conciliação por referência; nenhuma garantia falsa de exactly-once externo.
- [Sem fila instalada] → inbox/worker em PostgreSQL; documentar execução e backlog, não usar tarefa em memória como durabilidade.
- [E-mails nativos Asaas duplicam Resend] → novos clientes com `notificationDisabled=true`; não alterar cliente externo preexistente sem vínculo confirmado e revisão de política.
- [Snapshot obsoleto] → serializar conciliação por cobrança e comparar revisão, reconsultar após disputa.
- [Documentação muda] → revalidar contratos oficiais antes do código e do teste Sandbox.

## Migration Plan

Migration aditiva sobre cabeça real revalidada (atual `e9d3a8c2b170`), seguida da migration independente de Resend na mesma cadeia de integração. Criar tabelas/constraints/índices sem tocar dados clínicos. Alembic tem target_metadata=None: escrever operações explícitas e comparar modelos manualmente. Executar upgrade, integridade, concorrência e downgrade em banco descartável. Rollback operacional desliga integração e mantém dados financeiros; nunca executar downgrade destrutivo sobre histórico real.

## Revisão e decisões

Em 11/11/2026 o usuário aprovou Administrador/Financeiro emitirem e cancelarem, estorno restrito ao Administrador, demais roles sem acesso financeiro, uma cobrança ativa por Consulta, valor definido pelo operador e promoção de `/admin/financeiro` para área administrativa normal. Pix/boleto entram no escopo; cartão permanece pendente de homologação. Estorno integral será habilitado apenas no Pix suportado; boleto não usa endpoint não homologado.
