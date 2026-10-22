# Design — portais por perfil

## Limites de arquitetura

Reutilizar Reflex, SQLModel, PostgreSQL, sessão/RBAC, agendamento e atendimento existentes. A autorização é revalidada em application services a cada chamada. Nenhum handler aceita um profissional/paciente escolhido pelo cliente como identidade.

## Persistência

- Adicionar `PACIENTE` à constraint de roles sem reinterpretar usuários existentes.
- Adicionar `patients.user_id` nullable, único e FK restritiva para `auth_users.id`. Cadastros existentes permanecem sem portal.
- Adicionar convites persistidos com paciente, e-mail normalizado, hash SHA-256 do código aleatório, validade, consentimento/autor, estado de envio, uso/revogação e referência opcional ao provedor. O segredo em texto claro existe apenas durante o envio; nunca é salvo.
- Adicionar eventos de reagendamento com horário anterior/novo, autor e instante, gravados na mesma transação que move a consulta e reserva slots.
- Não duplicar e-mail na tabela Patient: a conta autenticada é a fonte canônica depois da ativação; o convite retém o destinatário necessário até o uso/expiração.

## Ativação

A Recepção inicia convite apenas após consentimento explícito. O e-mail contém um link público sem segredo e um código aleatório de uso único. Um formulário HTML nativo envia código, e-mail e senha por POST em corpo limitado para uma rota ASGI Starlette montada pelo próprio Reflex. A rota não grava os campos em Reflex State/eventos, não registra payload e não inclui o código na URL; cria User PACIENTE e liga Patient em uma transação. Respostas de falha não enumeram contas e não repetem entradas.

O serviço Resend existente é reutilizado com timeout, sem retry automático e estados `ACCEPTED`, `UNKNOWN`, `FAILED` e `NOT_CONFIGURED`. Sem envio confirmado, não há conta; a Recepção pode pedir novo convite em ação explícita.

## Consultas protegidas

- Médico: resolver exatamente o Professional ativo por `Professional.user_id == identity.id`; consultar somente suas consultas e pacientes derivados dessas consultas. Falhar fechado para vínculo ausente/inativo.
- Paciente: resolver Patient por `Patient.user_id == identity.id`; filtrar consultas por esse id no servidor. Não aceitar patient_id em query parameters, forms ou rota.
- Recepção: manter somente cadastro/contato operacional e agenda já autorizada; não carregar campos de ClinicalCareRecord/Prescription.
- Mostrar data/hora convertida pelo timezone IANA já configurado e status persistido. Consultas canceladas continuam no histórico; eventos de reagendamento preservam a data anterior.

## Endereço

Nome/endereço são lidos de `VITTA_ONE_CLINIC_NAME` e `VITTA_ONE_CLINIC_ADDRESS`. Se ausentes, o portal informa que a Administração ainda não configurou o endereço. Não há defaults de localização.

## Interface

Manter tokens, fonte, navegação e Reflex/Radix existentes. O Médico recebe Agenda/Pacientes; o Paciente recebe Minhas consultas. A agenda usa navegação por mês e lista acessível por teclado. Todos os estados de erro, vazio, carregamento, convite pendente, vínculo ausente e endereço ausente são explícitos. A Recepção mantém a separação entre cadastro, consentimento e fluxo de fila.

## Verificação

Testes de serviços/application com SQLite descartável e PostgreSQL descartável quando disponível, testes de fluxo de convite e autorização, migrations, OpenSpec e `reflex compile --dry`. Não executar Chromium, navegador, screenshot ou workflow browser.
