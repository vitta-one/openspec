# Proposal — Solicitações, resultados e anexos de exames

## Por que

O Vitta One já registra atendimento, prontuário e prescrições, mas não possui domínio de exame com solicitação, resultado ou anexo clínico persistido. A capacidade foi prevista no roadmap, sem implementação identificada na `develop`.

## O que muda

- Especificar pedidos de exame vinculados a paciente e episódio clínico autorizado (Consulta agendada ou QueueEntry avulsa).
- Registrar resultado e anexos vinculados, armazenando bytes no Cloudinary e metadados controlados em PostgreSQL.
- Definir validação de tamanho, tipo, conteúdo e credenciais de upload, permissões por recurso, tratamento de falhas e trilha de auditoria.
- Permitir leitura autorizada do resultado/histórico sem presumir integração com laboratórios.

## Capabilities

### New Capabilities

- `examination-management`: solicitação, resultado, anexos, leitura clínica, proteção e auditoria.

### Modified Capabilities

- `clinical-care-record` e `emergency-queue-clinical-care`: a integração será definida na etapa Apply, mediante delta explícito, sem alterar contratos vigentes nesta proposta.

## Fora do escopo

Integração com laboratórios, laudos por IA, dispositivos médicos, diagnóstico automático, compartilhamento público, armazenamento de prontuário em URL aberta, certificação ou uso clínico real.

## Decisões pendentes de aprovação

Tamanho/MIME permitidos; quem pode registrar resultado (autor Médico ou operador técnico habilitado); política de retenção/exclusão; estratégia de upload assinado vs proxy; estado de solicitação e resultado; acesso do Paciente ao anexo.

## Dependências e riscos

Exige autorização server-side por episódio, configuração Cloudinary exclusiva de backend, privacidade LGPD, transação para metadados, compensação de upload órfão e tratamento de objetos ausentes. Não aplicar migrations/integração até revisar design e decisões abertas.
