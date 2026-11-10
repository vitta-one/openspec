## MODIFIED Requirements

### Requirement: Prescrições só são mutáveis durante Consulta Em andamento
O sistema MUST aceitar mutações somente quando a Consultation relacionada estiver `EM_ANDAMENTO` e a Prescription ainda não tiver sido enviada para assinatura digital.

#### Scenario: Consulta concluída
- **WHEN** há tentativa de editar/adicionar/remover/excluir após `CONCLUIDA`
- **THEN** o servidor rejeita e preserva o histórico

#### Scenario: Consulta confirmada ainda aguardando
- **WHEN** há tentativa de criar Prescrição antes do atendimento iniciar
- **THEN** o servidor rejeita

#### Scenario: Consulta cancelada
- **WHEN** há tentativa de mutação em Consulta cancelada
- **THEN** o servidor rejeita

#### Scenario: Prescrição já enviada
- **WHEN** existe solicitação de assinatura para a Prescription
- **THEN** qualquer mutação de conteúdo ou exclusão é rejeitada mesmo que a Consulta continue em andamento

### Requirement: Visualização de impressão não implica assinatura digital
A versão imprimível MUST apresentar o estado real da assinatura digital e MUST exibir confirmação de assinatura somente quando validada pelo fluxo de integração. Sem solicitação ou sem integração configurada, MUST informar claramente que o documento não possui assinatura digital.

#### Scenario: Renderização imprimível
- **WHEN** a Prescription é exibida para impressão sem solicitação de assinatura
- **THEN** paciente, profissional, registro profissional, data da Consulta, itens e observações gerais são exibidos junto do aviso “Documento sem assinatura digital.”

#### Scenario: Assinatura pendente
- **WHEN** existe solicitação ainda não concluída
- **THEN** a visualização informa “Assinatura digital pendente” e não apresenta selo de documento assinado

#### Scenario: Assinatura confirmada
- **WHEN** o estado local foi reconciliado como assinado
- **THEN** a visualização informa assinatura confirmada e oferece acesso protegido ao documento final
