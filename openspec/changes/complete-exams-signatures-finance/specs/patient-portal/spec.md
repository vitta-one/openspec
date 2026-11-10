## Purpose

Oferecer ao Paciente uma área autenticada e responsiva para consultar exclusivamente a própria agenda, documentos liberados e obrigações financeiras.

## ADDED Requirements

### Requirement: Conta Paciente é vinculada a um único cadastro clínico
O sistema MUST associar a identidade Paciente a exatamente um cadastro de Paciente e MUST revalidar esse vínculo em toda leitura ou ação protegida.

#### Scenario: Paciente autenticado acessa o portal
- **WHEN** a sessão válida possui vínculo clínico ativo
- **THEN** o servidor carrega somente dados desse cadastro

#### Scenario: Vínculo ausente ou inativo
- **WHEN** a identidade não possui vínculo clínico válido
- **THEN** o portal nega dados e orienta contato com a clínica sem permitir escolha de outro Paciente

### Requirement: Portal apresenta agenda própria
O sistema MUST apresentar agendamentos futuros e histórico permitido do próprio Paciente, preservando as regras de agendamento e cancelamento existentes.

#### Scenario: Paciente possui consulta futura
- **WHEN** abre a agenda
- **THEN** visualiza data, horário, especialidade, profissional e estado da própria Consulta

### Requirement: Portal apresenta documentos e estados explicitamente disponíveis
O sistema MUST listar somente exames liberados e solicitações de assinatura de Prescrições vinculadas ao Paciente; documentos internos ou de terceiros MUST NOT ser retornados, e somente a Prescrição assinada MUST oferecer acesso ao arquivo final.

#### Scenario: Prescrição assinada disponível
- **WHEN** existe documento final assinado para Consulta do Paciente
- **THEN** o portal apresenta estado, data e ação protegida para obter o arquivo

#### Scenario: Prescrição ainda pendente
- **WHEN** existe solicitação de assinatura vinculada ao Paciente sem documento final
- **THEN** o portal apresenta somente o estado pendente, sem link ou arquivo fictício

#### Scenario: Exame não liberado
- **WHEN** anexo existe mas não foi liberado ao Paciente
- **THEN** ele não aparece em lista, contagem ou busca do portal

### Requirement: Portal apresenta situação financeira própria
O sistema MUST mostrar contas, vencimentos, valores, estados e links hospedados de cobrança somente do Paciente atual, sem permitir mutações administrativas.

#### Scenario: Cobrança em aberto
- **WHEN** Paciente abre a área financeira
- **THEN** visualiza valor, vencimento, forma e ação de pagamento fornecida pelo provedor

### Requirement: Portal mantém estados acessíveis e responsivos
O sistema MUST oferecer carregamento, vazio, erro e sucesso claros, navegação por teclado, foco visível e layout sem rolagem horizontal obrigatória em 320 px ou mais.

#### Scenario: Falha temporária de integração
- **WHEN** documentos ou cobrança externa não podem ser atualizados
- **THEN** o portal mantém dados locais seguros, informa indisponibilidade e oferece nova tentativa sem perder o contexto de foco

