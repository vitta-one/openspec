# Asaas Sandbox e Resend — configuração e operação

## Variáveis no deploy

O arquivo `.env.example` contém os nomes, sem credenciais. Configure as variáveis no backend do ambiente de teste; não preencha o exemplo versionado nem exponha os valores no navegador.

| Variável | Finalidade |
|---|---|
| DATABASE_URL | PostgreSQL do ambiente, preservando o contrato atual |
| VITTA_ONE_CLINIC_TIMEZONE | Fuso IANA, por exemplo America/Sao_Paulo |
| VITTA_ONE_SESSION_TTL_SECONDS | Duração positiva da sessão, por exemplo 3600 |
| VITTA_ONE_COOKIE_SECURE | true para HTTPS; false somente em localhost de QA |
| VITTA_ONE_PUBLIC_URL | Origem pública HTTPS usada no link do portal |
| ASAAS_API_KEY | Chave exclusivamente do Sandbox |
| ASAAS_BASE_URL | `https://api-sandbox.asaas.com/v3` |
| ASAAS_WEBHOOK_TOKEN | Token separado de 32–255 caracteres sem espaços, diferente da API key |
| RESEND_API_KEY | Chave de envio Resend |
| RESEND_FROM_EMAIL | Remetente do domínio verificado, como `Vitta-One <acesso@dominio-da-clinica>` |
| RESEND_WEBHOOK_SECRET | Secret de assinatura do webhook Resend/Svix, diferente da API key |

Nenhuma credencial real foi fornecida nesta implementação. Conforme orientação do usuário em 11/11/2026, o preenchimento e os testes reais ficam para o ambiente onde o deploy foi feito. A aplicação bloqueia chamadas ao Asaas de produção. Resend não é um simulador: ao configurar chave e remetente, qualquer envio é real; use apenas destinatários de teste autorizados na homologação.

## Banco

Aplicar a cadeia Alembic no PostgreSQL de teste após backup/revisão apropriados ao ambiente:

```text
python -m alembic heads
python -m alembic upgrade head
```

As migrations `f031a5aa5001` e `f031a5aa5002` adicionam cliente/cobrança/histórico/inbox, preferências/auditoria/outbox/tentativas e eventos de entrega. Não modificam tabelas clínicas. Não executar downgrade em ambiente que já contenha histórico financeiro ou notificações; para rollback operacional, parar o worker e desativar a integração, preservando os registros.

## Webhooks no backend Reflex

Registrar URLs finais sem redirecionamento, usando o endereço acessível do backend da aplicação (não presumir que o domínio do frontend encaminha `/api/`):

- Asaas: `POST /api/webhooks/asaas`, com authToken correspondente a ASAAS_WEBHOOK_TOKEN. O provedor envia `asaas-access-token`.
- Resend: `POST /api/webhooks/resend`, com secret de assinatura configurado em RESEND_WEBHOOK_SECRET. A assinatura Svix é validada sobre os bytes originais, com tolerância de 5 minutos.

Asaas: habilitar os eventos de criação/atualização/recebimento/confirmação/vencimento/exclusão/restauração/estorno necessários. O recebimento persiste evento mínimo e responde 200; não envia e-mail durante a requisição. Resend: habilitar email.delivered, email.bounced, email.failed e email.complained. O endpoint registra evidência autenticada; o worker vincula ao id da tentativa. Não registrar corpos completos nos logs do proxy.

## Processamento periódico

Configurar no ambiente de teste um processo agendado a cada cinco minutos:

```text
python -m vitta_one.integration_worker --limit 20
```

O comando executa um lote limitado e termina. Não é um serviço já instalado pelo código: o agendamento precisa existir no ambiente. As filas persistem no PostgreSQL; não dependem da memória do servidor web. Vários consumidores usam locks e SKIP LOCKED; monitorar backlog e eventos em REVIEW. Um evento financeiro com rede indisponível tenta novamente com backoff limitado; após 10 falhas vai para revisão. Tentativa de e-mail SENDING abandonada vira UNKNOWN, nunca é reenviada cegamente.

Como alternativa ao agendamento externo, configurar um processo separado e supervisionado com `python -m vitta_one.integration_worker --watch --limit 20`. Ele executa lotes a cada cinco minutos e encerra com interrupção. O servidor web não inicia esse processo automaticamente.

## Operação e critérios de segurança

- Administrador e Financeiro operam cobranças; estorno integral somente para Administrador e Pix recebido suportado. Não há estorno de boleto por endpoint não homologado nem cartão habilitado.
- Recepção e Médico não recebem acesso financeiro interno. `/admin/financeiro` é uma área administrativa normal; as outras prévias continuam limitadas ao QA.
- O valor é informado pelo operador autorizado. Uma cobrança não cancelada/não estornada bloqueia outra emissão para a mesma Consulta, inclusive quando UNKNOWN.
- Cliente financeiro é criado sob demanda. Depois de falha de cliente, usar atualização/conciliação; resultados ambíguos não autorizam outro POST.
- Pagamento recebido não conclui Consulta. Cancelamento da Consulta não cancela cobrança automaticamente.
- Na ficha do paciente/portal, registrar preferências separadas de agenda e financeiro. As escolhas começam desativadas e podem ser revogadas. Convite de ativação não é consentimento geral.
- Confirmação da reserva é emitida após AGENDADA. Check-in CONFIRMADA não repete essa mensagem. Lembrete é elegível entre 24h e 23h antes do horário atual; cancelamento/reagendamento invalida a revisão anterior.
- ACCEPTED significa aceitação da solicitação pelo Resend. DELIVERED exige webhook autenticado e indica confirmação do provedor, sem promessa de inbox.
- Reenvios financeiros podem ser revisados no painel de notificações. UNKNOWN exige revisão do resultado no provedor; mensagem já aceita/entregue não permite reenvio ordinário. Reemissão de acesso médico/paciente usa os fluxos originais para invalidar segredos anteriores.
- Recuperação pública de senha, cartão, aviso de vencimento e recibo/documento fiscal continuam fora do escopo homologado.

## Verificações

```text
python -m pytest tests/test_asaas_contract.py tests/test_financial_notifications.py tests/test_integration_migrations.py
reflex compile --dry
openspec validate integrate-asaas-financial --strict --no-interactive
openspec validate extend-resend-email --strict --no-interactive
```

Os testes de contrato usam provedores simulados e não substituem homologação. A suite de integrações também oferece execução em PostgreSQL quando DATABASE_URL está configurada e VITTA_ONE_QA_DISPOSABLE_DATABASE=yes; cria schema temporário próprio e o remove ao final. Não habilitar essa opção em banco de produção. QA de navegador desktop/mobile e execução real dos webhooks/provedores continuam necessários antes de aceite e arquivamento.
