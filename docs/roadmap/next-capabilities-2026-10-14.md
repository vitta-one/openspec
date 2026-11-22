# Vitta-One — planejamento de capabilities revisado (22/11/2026)

> Documento histórico de planejamento com escopo revisado para a entrega acadêmica de novembro de 2026. As changes descritas aqui foram arquivadas; este arquivo **não** atesta homologação externa. Os dados clínicos e financeiros usados em QA devem ser sintéticos.

## Situação e prioridade

O core possui autenticação/RBAC, gestão de profissionais e especialidades, agenda por horários pontuais, recepção/fila, atendimento, registro clínico e prescrições HTML imprimíveis. Os contratos canônicos existentes ficam em `openspec/specs/`. O escopo abaixo reúne os eixos efetivamente documentados no projeto e preserva o histórico de decisões, sem acrescentar novas integrações nesta entrega.

| Ordem | Próxima change (sugestão) | Dependências | Resultado esperado |
|---|---|---|---|
| 1 | `add-professional-email-onboarding` | Auth/RBAC, diretório, Resend | Cadastro médico simplificado e primeiro acesso seguro |
| 2 | `simplify-appointment-scheduling-ux` | Agenda, roles, histórico | Horários claros por profissional/dia, sem alterar arbitrariamente a regra de slot |
| 3 | `add-financial-payments` | Consulta, Asaas sandbox | Recebimentos e conciliação básica |
| 4 | `add-operational-dashboard` | Agenda, consultas, pagamentos (parciais) | KPIs baseados em dados persistidos |

## 1. Professional onboarding (próxima change)

**Problema:** o formulário administrativo atual exige um identificador manual e vínculo de conta previamente criada. A conta deve ser criada a partir de nome, e-mail e especialidades, com senha temporária ou convite.

**Requisitos planejados:** criação transacional de identidade `MEDICO`, profissional e associações; e-mail normalizado e único; reutilização controlada de conta MEDICO pré-existente; identificador interno gerado sem confundir com CRM; expiração e troca obrigatória de credencial inicial; não salvar nem registrar senha em claro; envio Resend server-side; status real e recuperação idempotente após falha; autorização ADMINISTRADOR; rollback de erro parcial; nenhuma alteração das credenciais dos usuários legados.

**Cenários de aceitação:** create válido, e-mail duplicado (médico já vinculado e outro perfil), especialidade inativa, reenvio idempotente, dois submits simultâneos, timeout/429/500 do provedor, API key ausente, senha expirada, primeiro acesso e logout, médico sem conta, falha após commit local.

**Riscos/decisões:** transmissão de senha por e-mail é inerentemente menos segura; preferir convite com token de uso único se o fluxo exigir produção. Definir política TTL/ativação/reenviar, limites e propriedade do endereço remetente antes da homologação real. O uso de Resend só deverá afirmar "e-mail enviado" após confirmação adequada do provedor. Em QA, usar fake declarativo, sem envios reais.

## 2. Simplificação da agenda (próxima change)

**Problema:** usuário precisa entender "slot explícito" e filtros extensos. **Meta:** separar profissional → data → horários disponíveis.

**Requisitos planejados:** exibir data/hora em `America/Sao_Paulo`; agrupamento diário; seleção por botão acessível e texto de situação; navegação diária (opcional semanal); filtros úteis; operações já existentes de criar horário, agendar, reagendar, cancelar e confirmar chegada; carregamento progressivo; estados vazios e falhas legíveis. Não inferir duração, recorrência, turnos fixos, datas passadas elegíveis ou encaixes.

**Cenários de aceitação:** nenhum horário, horário lotado, filtro sem resultados, consulta concorrente tentando reservar mesmo horário, reagendamento inválido, reativação bloqueada, problemas DST/fuso, teclado e viewport móvel.

**Riscos/decisões:** decidir se a UI trabalha com uma data selecionada ou semana por padrão, sem alterar semântica atual de horários pontuais.

## 3. Financeiro Asaas (sandbox)

**Problema:** painel Financeiro atualmente é um shell. **Contrato pretendido:** lançamento de cobrança para consulta com regras explicitamente aprovadas, recepção de status de pagamento, listagem e filtros, conciliação simples, reversões e falhas, preservando RBAC Financeiro/Admin segundo contratos futuros.

**Cenários:** cobrança criada, duplicidade na mesma consulta, inadimplência, pagamento confirmado, webhook duplicado, 429/500, reprocessamento seguro, estorno, consulta cancelada antes/depois da cobrança.

**Decisões necessárias:** quem pode cobrar e alterar valores, tipos de cobrança, reembolso, regras de cancelamento, política de conciliação. Não inventar regras comerciais.

## 4. Dashboard gerencial

**Contrato pretendido:** indicadores derivados somente de dados reais, como consultas do dia, aguardando, concluídas e canceladas, profissionais ativos, e cobranças confirmadas quando implementadas. Cada KPI precisa ter definição de período, fuso, filtros, autorizações e fonte SQL rastreável.

**Cenários:** clínica vazia (zero honesto), período com dados, role sem permissão, dados simultâneos, dashboards paginados, cache invalidado após novas consultas e alterações no financeiro.

**Riscos:** evitar métricas ambíguas, N+1, vazamento clínico e duplicação de fonte de verdade.

## Governança de implementação

- Manter uma change prioritária ativa de cada vez, com dependências documentadas.
- Nunca arquivar por contagem de checkboxes: exigir OpenSpec strict, testes Python, PostgreSQL 16, Reflex compile e QA de navegador para mudanças visuais.
- Arquivar apenas depois de revisão de diff e evidências; sincronizar specs sem apagar requisitos anteriores.
- No ambiente local do usuário, usar o PostgreSQL de QA isolado da porta 55432. Não modificar dados existentes sem autorização específica.
