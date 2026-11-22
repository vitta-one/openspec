# Spec Delta — E-mails transacionais

## Purpose

Fornecer mensagens transacionais acessíveis e seguras, preservando o onboarding existente e autorizando explicitamente destinatários e novos gatilhos.

## ADDED Requirements

### Requirement: Compatibilidade de acesso médico e paciente
O sistema MUST preservar criação de credencial médica temporária e convite de paciente consentido, com expiração de 24 horas, troca inicial obrigatória e código de ativação de uso único. Reemissão MUST preservar autorização, invalidar o segredo anterior e respeitar intervalo mínimo de 2 minutos para paciente. Senhas e códigos MUST existir somente na memória necessária ao envio.

#### Scenario: Boas-vindas ao médico
- **GIVEN** Administrador cria médico no fluxo normal
- **WHEN** uma nova credencial temporária é gerada
- **THEN** envia as instruções existentes, preserva expiração e troca obrigatória, e registra somente metadados seguros de tentativa.

#### Scenario: Convite de paciente
- **GIVEN** Recepcionista autorizada e consentimento explícito por convite
- **WHEN** destinatário é válido e ainda não há conta vinculada
- **THEN** gera código de uso único por 24 horas e solicita envio sem persistir o código ou corpo do e-mail.

#### Scenario: Reenvio antecipado e código antigo
- **WHEN** convite é repetido antes de 2 minutos ou código revogado/expirado é apresentado
- **THEN** o servidor recusa a operação e não ativa conta nem repete envio.

#### Scenario: Onboarding em QA com senha escolhida
- **WHEN** cadastro médico usa o fluxo QA local já autorizado
- **THEN** não envia senha por e-mail nem gera credencial temporária desnecessária.

### Requirement: Templates seguros e acessíveis
O sistema MUST usar layout consistente, HTML escapado, texto alternativo, leitura móvel e link descritivo. MUST permitir somente URLs HTTPS de origem autorizada, exceto localhost em QA. Templates MUST cobrir médico, paciente e os gatilhos aprovados de agenda/financeiro. Recuperação de senha MUST permanecer indisponível até existir fluxo seguro aprovado, sem link fictício.

#### Scenario: Escape de HTML e URL
- **WHEN** nome contém tags e um campo de link contém conteúdo malicioso
- **THEN** o nome é apresentado como texto e o link é recusado, sem injeção de HTML ou esquema javascript.

#### Scenario: Leitura móvel
- **WHEN** mensagem é aberta em largura de 320 px com imagens bloqueadas
- **THEN** conteúdo e ação permanecem legíveis, com finalidade compreensível em texto.

#### Scenario: Recuperação inexistente
- **WHEN** usuário tenta solicitar template/link de recuperação sem fluxo aprovado
- **THEN** o sistema não emite token nem anuncia funcionalidade disponível.

### Requirement: Preferências específicas e destinatário revalidado
O sistema MUST registrar preferência explícita, revogável e auditável separada para agenda e financeiro. Consentimento de convite MUST NOT ser reutilizado como autorização geral. Somente paciente vinculado autenticado ou Recepcionista com declaração explícita do paciente MUST poder registrar a preferência; mutações MUST revalidar identidade e vínculo no servidor.

#### Scenario: Preferência válida
- **WHEN** paciente autenticado altera a própria preferência ou Recepcionista registra autorização expressa
- **THEN** persiste finalidade, data e autor, sem habilitar a outra finalidade implicitamente.

#### Scenario: Tentativa sem autorização
- **WHEN** Médico, Financeiro ou paciente de outro cadastro tenta alterar preferências
- **THEN** a operação é negada antes de gravar ou enviar e-mail.

#### Scenario: Destinatário inválido ou alterado
- **WHEN** endereço não é válido ou não corresponde ao vínculo atual no envio
- **THEN** a notificação é suprimida ou encaminhada à revisão, sem usar outro destinatário fornecido pelo navegador.

### Requirement: Privacidade e configuração de remetente
O sistema MUST manter API key e remetente em configuração do backend. Logs, histórico e estado cliente MUST NOT conter senhas, códigos, tokens, corpo HTML, prontuários ou diagnósticos. Mensagens MUST minimizar informações pessoais. Ausência de configuração MUST ser exposta como NOT_CONFIGURED sem alegar envio ou entrega.

#### Scenario: Falta de configuração
- **WHEN** chave ou remetente está ausente
- **THEN** não chama Resend e registra NOT_CONFIGURED sem afetar o cadastro/agendamento/pagamento já persistido.

#### Scenario: Auditoria de privacidade
- **WHEN** evento de comunicação é auditado
- **THEN** apresenta tipo, identificador, provedor, timestamps e estado, sem segredo, conteúdo clínico ou mensagem integral.
