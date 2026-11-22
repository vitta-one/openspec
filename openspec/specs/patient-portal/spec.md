# patient-portal Specification

## Purpose

Oferecer ao paciente autenticado uma visão exclusivamente operacional de suas consultas e da localização verdadeira da clínica, sem expor dados clínicos protegidos.

## Requirements

### Requirement: Portal de consulta próprio
O portal MUST derivar o paciente exclusivamente da sessão PACIENTE e listar consultas futuras e passadas somente daquele vínculo.

#### Scenario: Paciente consulta a própria agenda
- **WHEN** um paciente autenticado abre um mês/período
- **THEN** vê suas consultas com médico, especialidades disponíveis, data/hora local, status persistido e dados configurados da clínica

#### Scenario: ID de outro paciente
- **WHEN** a sessão altera parâmetros, IDs ou estado para apontar para outra pessoa
- **THEN** a consulta é rejeitada/ignorada e nenhum dado alheio é retornado

#### Scenario: Sem consultas
- **WHEN** o paciente não possui consultas no período
- **THEN** o portal mostra estado vazio verdadeiro e permite navegar para outro período

### Requirement: Reagendamentos preservam histórico visível
O sistema MUST gravar a data anterior e a nova data na mesma transação do reagendamento.

#### Scenario: Consulta reagendada
- **WHEN** a Recepção muda a data de uma consulta
- **THEN** a agenda do paciente mostra a data atual e informa a alteração anterior sem apagar o histórico

### Requirement: Consulta cancelada não desaparece
O sistema MUST exibir o status CANCELADA e a data do compromisso cancelado no histórico do paciente.

#### Scenario: Consulta cancelada
- **WHEN** uma consulta foi cancelada
- **THEN** o paciente pode reconhecê-la como cancelada e não a confunde com compromisso ativo

### Requirement: Endereço verdadeiro da clínica
O sistema MUST exibir nome/endereço institucionais reais do PostgreSQL nas próximas leituras do portal, com fallback opcional para configuração válida de implantação somente quando não há dado persistido.

#### Scenario: Endereço ausente
- **WHEN** nome/endereço não estão persistidos nem existem valores legados válidos
- **THEN** a UI informa que a Administração ainda precisa configurar o local e não mostra endereço de exemplo

#### Scenario: Administração atualiza o endereço
- **WHEN** o Administrador salva dados válidos no banco
- **THEN** o portal exibe os dados atualizados na próxima leitura sem reinício da aplicação e sem substituir o logotipo Vitta One


### Requirement: Portal não expõe conteúdo clínico
O portal MUST NOT retornar sintomas, ClinicalCareRecord, histórico clínico, diagnóstico, conduta, Prescription ou itens de Prescrição.

#### Scenario: Paciente abre consulta
- **WHEN** o portal carrega detalhes
- **THEN** apresenta apenas dados operacionais da consulta e clínica

### Requirement: Ativação de portal exige convite válido e consentimento explícito
O sistema MUST vincular conta PACIENTE ao cadastro correto somente mediante convite elegível, consentimento registrado e confirmação segura, impedindo reutilização de código, duplicação de identidade e identificação pública da existência de conta.

#### Scenario: Convite válido e ativação
- **WHEN** o paciente possui convite não expirado, ainda não usado e seus dados de ativação são validados no servidor
- **THEN** o vínculo com a identidade PACIENTE é persistido sem criar segundo cadastro de paciente

#### Scenario: Convite expirado ou utilizado
- **WHEN** um código expirado, revogado ou já consumido é apresentado novamente
- **THEN** a ativação é recusada de forma genérica, sem permitir acesso ao portal

#### Scenario: Consentimento ausente
- **WHEN** o fluxo de convite não possui consentimento exigido
- **THEN** o servidor recusa iniciar a ativação

#### Scenario: Falha de e-mail
- **WHEN** o transporte de convite está indisponível ou retorna estado desconhecido
- **THEN** o sistema registra um estado coerente e não afirma entrega confirmada nem duplica a conta

### Requirement: Portal utiliza apenas informações da própria sessão ativa
O portal MUST revalidar a identidade PACIENTE e o vínculo Patient a cada leitura e ação de reserva; uma sessão sem vínculo ou expirada MUST NOT projetar consultas de outro paciente.

#### Scenario: Sessão inválida
- **WHEN** o paciente perde a sessão durante navegação ou tentativa de reserva
- **THEN** o servidor recusa a operação e limpa o estado sensível apresentado
