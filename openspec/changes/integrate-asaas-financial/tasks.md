# Tasks — Financeiro Asaas

## 1. Explore, Propose e Review

- [x] 1.1 Auditar fontes, domínio, migrations, autorização, testes e 22 changes ativas; verificar diagnóstico e matriz em `docs/auditoria-asaas-resend-2026-11-11.md`.
- [x] 1.2 Criar proposta, três specs e design; conferir arquivos e validação strict do OpenSpec.
- [x] 1.3 Registrar aprovações de permissões, cobrança única, valor e rota administrativa; conferir decisões no design e nas respostas de 11/11/2026.
- [x] 1.4 Revisar rastreabilidade requisito/tarefa, integrações oficiais e conflitos; verificar relatório de revisão e validar change completa com `openspec validate integrate-asaas-financial --strict --no-interactive`.

## 2. Fundação e persistência

- [ ] 2.1 Preparar Python 3.12/venv e dependências existentes conforme instruções Reflex; verificar versões e imports sem modificar framework.
- [ ] 2.2 Criar modelos de cliente, cobrança, histórico e inbox com unicidade/valor/FKs; testar constraints e serialização sem segredos.
- [ ] 2.3 Escrever migration aditiva encadeada e registrar modelos; verificar upgrade/downgrade em PostgreSQL descartável e Alembic heads.
- [ ] 2.4 Implementar guard financeiro para sessão, roles e troca inicial; testar todas as roles, token ausente/expirado e chamada direta.

## 3. Contratos Asaas

- [ ] 3.1 Implementar adaptador httpx/configuração Sandbox, timeouts, headers, erros e validação de respostas; testar ausência de configuração, produção bloqueada, 4xx/429/5xx, JSON inválido, timeout e logs mínimos.
- [ ] 3.2 Implementar criação/atualização de cliente por referência com intenção durável; testar cliente reutilizado, ambiguidade, dados inválidos, concorrência e timeout seguido de conciliação.
- [ ] 3.3 Implementar emissão/consulta de Pix e boleto, link validado e QR Pix; testar valor/vencimento/método/Consulta inválidos, emissão duplicada e resultado incerto sem novo POST.
- [ ] 3.4 Implementar cancelamento e estorno integral Pix com intenção e confirmação; testar role, estado atual, corrida de recebimento, saldo insuficiente, timeout e método não suportado.
- [ ] 3.5 Documentar variáveis sem segredos e procedimento de conciliação; verificar exemplos contra contratos oficiais.

## 4. Inbox, processamento e comunicação

- [ ] 4.1 Integrar endpoint Asaas à API Reflex existente, token constante, limite e persistência; testar 200/400/401/413/503 e duplicidade concorrente.
- [ ] 4.2 Implementar worker com lease, SKIP LOCKED, backoff e conciliação serializada por cobrança; testar fora de ordem, cobrança não vinculada, valor divergente, falha temporária e reinício.
- [ ] 4.3 Persistir transição/histórico/evento atomicamente e publicar evento elegível para Resend; testar rollback, primeira transição RECEIVED e preservação da Consulta.
- [ ] 4.4 Documentar execução do worker e operação do backlog/UNKNOWN; verificar comando em ambiente de teste.

## 5. Painéis financeiros

- [ ] 5.1 Implementar projeções SQL com resumo, evolução diária, filtros combinados, paginação estável e detalhes; testar valores conhecidos, recortes temporais, lista vazia, erro e histórico.
- [ ] 5.2 Integrar State e componentes reais em `/financeiro`; verificar autorização em toda ação, formulário válido/inválido, Pix/boleto e confirmações.
- [ ] 5.3 Integrar `/admin/financeiro` sem flag QA e preservar guards dos outros previews; testar acesso, navegação e regressões administrativas.
- [ ] 5.4 Verificar desktop/mobile/teclado e estados loading/erro/vazio/sucesso em navegador; registrar evidências e ajustar acessibilidade.

## 6. Verify integrado

- [ ] 6.1 Executar suites relevantes existentes e contratos novos; registrar contagens reais de aprovados/falhas/skips.
- [ ] 6.2 Executar concorrência, transações, migrations e outbox financeira em PostgreSQL; registrar evidência sem confundir SQLite com PostgreSQL.
- [ ] 6.3 Executar `reflex compile --dry` e E2E login → paciente → agenda → cobrança → webhook → histórico/notificação; registrar desktop/mobile.
- [ ] 6.4 Homologar cliente/Pix/boleto, consulta, webhook, cancelamento e estorno suportado em Asaas Sandbox com configuração autorizada; registrar IDs sintéticos/resultados sem chaves.
- [ ] 6.5 Comparar código/specs/tasks, executar validação strict final e preparar PR com limitações; manter pendências abertas se faltar evidência.

## Workflow follow-up

- Sincronizar specs e arquivar oficialmente somente após todas as tarefas e critérios de aceite verificados.
- Conferir histórico arquivado e specs consolidadas sem placeholders; não arquivar outras changes ativas.
