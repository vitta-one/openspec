# Vitta-One — sequência de capabilities após o QA (14/10/2026)

> Documento de planejamento e pré-especificação, **não** uma spec canônica concluída. Não abrir todas as changes ao mesmo tempo. Qualquer decisão abaixo ainda não implementada exige proposal, design, spec delta, tasks, QA e archive próprios. Os dados clínicos e financeiros usados em QA devem ser sintéticos.

## Situação e prioridade

O core possui autenticação/RBAC, gestão de profissionais e especialidades, agenda por horários pontuais, recepção/fila, atendimento, registro clínico e prescrições HTML imprimíveis. Os contratos canônicos existentes ficam em `openspec/specs/`. As dependências futuras abaixo devem preservar a consistência do domínio e a segurança.

| Ordem | Próxima change (sugestão) | Dependências | Resultado esperado |
|---|---|---|---|
| 1 | `add-professional-email-onboarding` | Auth/RBAC, diretório, Resend | Cadastro médico simplificado e primeiro acesso seguro |
| 2 | `simplify-appointment-scheduling-ux` | Agenda, roles, histórico | Horários claros por profissional/dia, sem alterar arbitrariamente a regra de slot |
| 3 | `add-examination-attachments` | Atendimentos concluídos/ativos, Cloudinary | Solicitações, resultados e anexos auditáveis |
| 4 | `add-prescription-signature` | Prescrição estruturada, ZapSign sandbox | Assinatura demonstrativa e rastreamento de estados |
| 5 | `add-financial-payments` | Consulta, Asaas sandbox | Recebimentos e conciliação básica |
| 6 | `add-operational-dashboard` | Agenda, consultas, pagamentos (parciais) | KPIs baseados em dados persistidos |

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

## 3. Exames e anexos Cloudinary

**Problema:** clínica precisa registrar solicitação e resultados no contexto clínico. **Contrato pretendido:** vínculo por atendimento/consulta/paciente/médico; autorização no servidor; upload assinado diretamente ou proxy seguro; metadados persistidos separados do arquivo; limitação MIME/tamanho/extensões; auditoria; gestão de falhas; leitura do histórico; sem integração com laboratórios externos.

**Cenários:** anexos válidos e inválidos, upload cancelado, erro de rede, documento externo removido, médico não responsável, paciente de outro contexto, tentativa de path traversal e arquivo malicioso. Planejar retenção e remoção reversível.

**Dependências:** desenho de modelos e política de armazenamento/retenção; configuração Cloudinary. Não colocar credenciais em cliente nem URLs privadas em logs.

## 4. Assinatura de prescrições ZapSign (sandbox)

**Problema:** prescrição atual é um HTML imprimível sem assinatura digital, sem selo ou QR real. **Contrato pretendido:** vincular uma prescrição imutável e autor autorizado ao documento enviado; estados rascunho/enviado/assinado/falhou/cancelado coerentes com ZapSign; validação de webhook autenticado; idempotência; trilha de auditoria; permitir reconsulta sem presumir validade jurídica.

**Cenários:** envio e confirmação sandbox, webhook duplicado ou fora de ordem, timeout, reenvio, link expirado, alterações após início da assinatura, médico distinto, sessão expirada.

**Riscos:** requisitos jurídicos fora do escopo acadêmico; não mostrar "assinado" sem confirmação do provedor.

## 5. Financeiro Asaas (sandbox)

**Problema:** painel Financeiro atualmente é um shell. **Contrato pretendido:** lançamento de cobrança para consulta com regras explicitamente aprovadas, recepção de status de pagamento, listagem e filtros, conciliação simples, reversões e falhas, preservando RBAC Financeiro/Admin segundo contratos futuros.

**Cenários:** cobrança criada, duplicidade na mesma consulta, inadimplência, pagamento confirmado, webhook duplicado, 429/500, reprocessamento seguro, estorno, consulta cancelada antes/depois da cobrança.

**Decisões necessárias:** quem pode cobrar e alterar valores, tipos de cobrança, reembolso, regras de cancelamento, política de conciliação. Não inventar regras comerciais.

## 6. Dashboard gerencial

**Contrato pretendido:** indicadores derivados somente de dados reais, como consultas do dia, aguardando, concluídas e canceladas, profissionais ativos, e cobranças confirmadas quando implementadas. Cada KPI precisa ter definição de período, fuso, filtros, autorizações e fonte SQL rastreável.

**Cenários:** clínica vazia (zero honesto), período com dados, role sem permissão, dados simultâneos, dashboards paginados, cache invalidado após novas consultas e alterações no financeiro.

**Riscos:** evitar métricas ambíguas, N+1, vazamento clínico e duplicação de fonte de verdade.

## Governança de implementação

- Manter uma change prioritária ativa de cada vez, com dependências documentadas.
- Nunca arquivar por contagem de checkboxes: exigir OpenSpec strict, testes Python, PostgreSQL 16, Reflex compile e QA de navegador para mudanças visuais.
- Arquivar apenas depois de revisão de diff e evidências; sincronizar specs sem apagar requisitos anteriores.
- No ambiente local do usuário, usar o PostgreSQL de QA isolado da porta 55432. Não modificar dados existentes sem autorização específica.
