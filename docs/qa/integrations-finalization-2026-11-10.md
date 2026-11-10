# Homologação — anexos, assinatura e financeiro

Data da execução: 10/11/2026.

## Escopo validado localmente

- modelos, regras e adapters sem rede real;
- autorização por role, Médico autor e Paciente proprietário;
- anexos privados, liberação explícita e links temporários;
- bloqueio da Prescrição após a solicitação de assinatura;
- deduplicação e monotonicidade dos webhooks;
- cálculos financeiros em centavos, conta própria do Paciente e reconciliação segura;
- renderização isolada dos componentes Reflex alterados.

## Evidências automatizadas

- 33 testes direcionados de adapters, anexos, assinatura, financeiro, webhooks e autorização: aprovados;
- suíte sem os quatro arquivos explicitamente dependentes de PostgreSQL: **462 aprovados, 1 ignorado**;
- suíte completa: **461 aprovados, 1 ignorado e 16 falhas** na primeira execução; 15 eram exclusivamente recusa de conexão PostgreSQL e a falha unitária restante foi corrigida e revalidada na suíte sem PostgreSQL;
- `python -m compileall`, importação da aplicação e renderização isolada dos seis componentes alterados: aprovados;
- geração SQL offline do Alembic para upgrade até `f4a9c2d7e610` e downgrade até `e9d3a8c2b170`: aprovada, com um único head.

## Limitações deste ambiente

- PostgreSQL/Docker não estavam disponíveis em `127.0.0.1:55432`; por isso upgrade/downgrade real da migration e os 15 testes de concorrência/constraints PostgreSQL permanecem para QA isolado;
- Cloudinary, ZapSign e Asaas Sandbox não receberam credenciais reais; nenhum resultado externo é alegado;
- `reflex compile --dry` iniciou a preparação do frontend, mas o ambiente tentou acessar telemetria/destinos externos não autorizados e a execução foi interrompida. Componentes alterados foram construídos e renderizados isoladamente;
- QA Chromium nas larguras 320, 375, 768 e 1280 px depende de aplicação e banco QA ativos.

## Roteiro de aceite Sandbox

1. Aplicar `alembic upgrade head` em PostgreSQL 16 descartável, executar downgrade desta revisão e novo upgrade.
2. Cadastrar identidades sintéticas para Médico, Paciente e Financeiro.
3. Anexar PDF/JPEG/PNG válido; rejeitar extensão, MIME e tamanho inválidos; confirmar acesso negado antes da liberação e link expirável depois dela.
4. Enviar Prescrição uma vez; repetir ação; confirmar um único documento, bloqueio de edição, webhook repetido e evento final fora de ordem.
5. Emitir conta; gerar Pix/boleto; simular timeout e usar **Verificar no Asaas**; reenviar evento de pagamento e confirmar um único `PaymentRecord`.
6. Entrar como outro Paciente/Médico e confirmar `403`/redirecionamento sem vazamento de existência do recurso.
7. Executar `reflex compile --dry`, a suíte Pytest completa e o roteiro Chromium responsivo.

Não promover para produção sem concluir esses itens e registrar as evidências do ambiente Sandbox.
