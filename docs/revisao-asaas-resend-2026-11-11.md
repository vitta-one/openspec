# Review — Asaas e Resend — 11/11/2026

## Resultado

As duas changes têm proposal, design, tasks e três capabilities cada. `openspec validate <change> --strict --no-interactive` passou para ambas no OpenSpec 1.14.1. `openspec status` confirma 4/4 artefatos por change; isso indica planejamento completo, não implementação completa. Nenhuma spec consolidada foi antecipada nem change arquivada.

## Aprovações registradas

O usuário aprovou nesta conversa: Administrador e Financeiro emitem e cancelam; somente Administrador solicita estorno integral; Recepcionista e Médico sem acesso financeiro. Novos e-mails exigem autorização registrada, com confirmação, reagendamento, cancelamento, cobrança disponível, pagamento confirmado e lembrete 24h. Confirmação significa reserva AGENDADA. Uma cobrança ativa por Consulta, valor informado pelo operador autorizado e `/admin/financeiro` normal, sem flag de preview QA. Cartão e recuperação de senha permanecem pendentes de homologação.

## Revisão técnica e rastreabilidade

| Contrato | Tarefas financeiras | Tarefas de comunicação |
|---|---|---|
| Autorização e privacidade | 2.4, 5.2–5.3 | 2.3, 3.2–3.3, 5.3 |
| Cliente único, dados inválidos e recuperação | 3.1–3.2 | — |
| Pix/boleto, método indisponível e consulta | 3.3 | — |
| Cancelamento e estorno autorizado | 3.4 | 4.4 |
| Webhook autêntico, duplicado, fora de ordem | 4.1–4.2 | 5.1–5.2 |
| Estados e independência clínica | 4.3 | 4.2, 4.4 |
| Persistência, integridade e concorrência | 2.2–2.3, 6.2 | 3.1, 4.1, 6.2 |
| Resumo/listagem/histórico/evolução | 5.1 | — |
| UI desktop/mobile e erro/vazio | 5.2–5.4 | 2.2, 3.2, 6.3 |
| Templates e acesso médico/paciente | — | 2.1–2.4 |
| Preferências e destinatários | 4.3 | 3.2, 4.2–4.4 |
| Timeout = UNKNOWN e retry manual | 3.1–3.4 | 2.1, 3.3, 4.1 |
| Lembretes e revisão de horário | — | 4.3 |
| Aceitação/entrega e assinatura | — | 5.1–5.2 |
| Verificação integrada e homologação | 6.1–6.5 | 6.1–6.5 |

Todos os requisitos possuem cenários WHEN/THEN, com estado inicial quando relevante. Descrições passaram o limite strict. Há cenários explícitos para dados inválidos, acesso indevido, concorrência, indisponibilidade, token ausente, timeout, reenvio, cancelamento e configuração ausente.

Migrations devem ser aditivas, com constraints e índices explícitos; cabeça atual `e9d3a8c2b170`. Não duplicar Patient/Consulta/dados clínicos. Não aplicar alteração destrutiva em banco existente. Extração de transporte mantém os dois senders públicos e seus testes. Inbox/outbox persistentes impedem acoplamento entre webhook Asaas e latência do Resend. Não inventar idempotência Asaas por externalReference.

## Conflitos tratados e alternativas

- Identificado descompasso entre roles da spec inicial e código PACIENTE; não alterar enum nem remover role. Testar paciente como acesso financeiro negado.
- Rotas QA existentes: somente financeiro muda de categoria por aprovação; demais prévias preservam flag e autorização.
- Onboarding com senha temporária não vai à outbox com corpo: manter segredo transitório e registrar metadados; mudanças de convite/funcionário ativas conservam contratos.
- Agenda usa commit interno: intenção deve ser inserida no serviço antes do commit, incluindo fluxo do portal, evitando envio duplicado nos States.
- Nova preferência de comunicação não herda consentimento de ativação. Default false e revalidação antes de envio.
- Estorno inicial limitado a Pix suportado; boleto e cartão não usam endpoints não homologados.

## Verify pendente

A revisão estática e validação OpenSpec estão concluídas. Preparação do runtime Python 3.12 isolado está em andamento; o app fornece Python 3.12.14 embora o comando global python seja um alias sem instalação. Testes unitários/integração/E2E, compile, migrations e chamadas reais ainda não foram executados nesta revisão. Banco isolado, configuração Sandbox e destinatário de teste autorizado serão necessários para homologação real. Não há autorização de produção.

## Decisão de passagem

Pode iniciar Apply dos comportamentos aprovados e dos testes locais. Homologação externa e archive continuam condicionados às evidências reais. A missão explícita de prosseguir após Review prevalece sobre a orientação genérica de planejamento isolado do workflow local.
