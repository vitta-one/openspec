## Why

O Vitta One já possui o fluxo clínico central, porém exames/anexos, assinatura digital de prescrições e financeiro continuam apenas planejados. Isso impede homologar a jornada completa da clínica e mantém o painel Financeiro, o prontuário documental e a entrega de prescrições sem operações reais.

## What Changes

- Adicionar exames e anexos clínicos com metadados persistidos, upload privado no Cloudinary, autorização por vínculo, auditoria e indisponibilidade segura sem credenciais.
- Adicionar assinatura digital de prescrições no ZapSign, com estados locais explícitos, envio idempotente, webhook autenticado, reconciliação e acesso ao documento assinado sem persistir URLs temporárias como fonte de verdade.
- Adicionar módulo financeiro com serviços/procedimentos, contas, cobranças e pagamentos, integração Asaas Sandbox, idempotência, conciliação por webhook e dashboard calculado somente com dados persistidos.
- Consolidar o portal do paciente como capability protegida para o próprio paciente consultar agenda, documentos liberados e situação financeira, sem expor dados de terceiros.
- Atualizar o contrato de prescrição para substituir o aviso de ausência de assinatura por estados reais quando a integração estiver configurada, preservando modo local honesto quando estiver indisponível.
- Atualizar RBAC para refletir a role Paciente já existente no código e proteger, no servidor, leituras e mutações dos novos recursos.
- Documentar variáveis de ambiente, diagnóstico seguro das integrações, operação Sandbox e comportamento degradado.

## Capabilities

### New Capabilities

- `clinical-exam-attachment`: cadastro, armazenamento, consulta, download e auditoria de exames e anexos clínicos.
- `prescription-digital-signature`: ciclo de envio, assinatura, webhook e recuperação do documento assinado no ZapSign.
- `financial-billing`: catálogo de serviços, contas, cobranças, pagamentos, conciliação e indicadores financeiros reais.
- `patient-portal`: acesso autenticado e restrito do paciente à própria agenda, documentos clínicos liberados e situação financeira.

### Modified Capabilities

- `clinical-prescription`: incluir estados de assinatura, imutabilidade após envio e visualização protegida do documento assinado.
- `access-control`: reconhecer a role Paciente e explicitar autorização por recurso para exames, prescrições assinadas e dados financeiros.

## Impact

- Novos modelos SQLModel/SQLAlchemy, índices, constraints e migrations Alembic.
- Novos módulos de domínio/aplicação/estado/UI sob `vitta_one/`, sem substituir Reflex.
- Clientes HTTP isolados para Cloudinary, ZapSign e Asaas, usando `httpx`, timeouts, erros normalizados e segredos apenas no ambiente.
- Novas superfícies protegidas para Médico, Recepção, Financeiro e Paciente, além de rotas de webhook específicas já suportadas pela aplicação Reflex.
- Testes unitários, autorização, idempotência, webhooks, concorrência, compile Reflex e documentação operacional.
- Sem integração com laboratório externo, sem processamento direto de cartão e sem movimentação financeira real; Asaas permanece em Sandbox nesta change.
