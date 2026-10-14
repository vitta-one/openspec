## Escolhas

1. `User` recebe `must_change_password` e `temporary_password_expires_at` com backfill seguro para usuários legados (`false`/NULL).
2. `Professional` recebe `onboarding_email_status` (NOT_REQUIRED / PENDING / ACCEPTED / NOT_CONFIGURED / FAILED / UNKNOWN) e ID do e-mail aceito quando aplicável. Não indica leitura/delivery.
3. `register_medical_professional` valida dados, cria usuário/associação numa única transação e retorna segredo temporário **somente em memória do servidor**. Conta Médica pré-existente é reaproveitada sem mudar senha.
4. Um adaptador de e-mail `ResendMailSender` usa o endpoint oficial REST via httpx com timeout, TLS, `Idempotency-Key` por operação, dados mínimos e nunca registra chave, senha ou payload.
5. Tratamento de falha no envio pós-commit altera somente status. Não reenvia automaticamente uma senha que não pode ser persistida em claro; reemissão precisa de operação explicitamente autorizada, com rotação de hash/TTL e nova chave, e será um cenário separado de aceite.
6. Conta com senha temporária só pode acessar a rota de troca; todas as operações de domínio protegidas por `require_role` são negadas até alteração efetiva. Sessão provisória fica fora do shell clínico.
7. `AuthState` controla a tela de troca obrigatória sem expor senha anterior em State persistido. Erros genéricos de senha e validações server-side.
8. Sem Resend configurado, persistir status NOT_CONFIGURED e mostrar no Admin "Conta criada; e-mail não enviado". Não produzir sucesso falso.

## Testes
- Serviço: criação, validação e unicidade, rollback, vínculo de conta existente, senha hash/expiração.
- RBAC: não Admin negado, conta provisória negada nas capabilities, primeira troca obrigatória.
- HTTP: fake com resposta aceita, 4xx, 5xx, timeout, 429 e sem env, sem chamadas reais.
- Migrations no PostgreSQL 16 isolado, Pytest, Reflex compile, navegador/mobile.
- Testes com IDs/CPFs fictícios; não armazenar credenciais em evidências.

## Rollout
Executar migration primeiro em banco descartável; só propor aplicação em ambiente real com backup/dry-run e autorização. Não destruir informação anterior.
