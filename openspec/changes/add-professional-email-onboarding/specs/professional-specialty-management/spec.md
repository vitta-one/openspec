## MODIFIED Requirements

### Requirement: Administrador gerencia profissionais
O sistema MUST permitir cadastrar profissional com nome, e-mail único e ao menos uma especialidade ativa sem pedir identificador interno nem vínculo manual de conta. MUST gerar identificador interno único, sem simular CRM, e vincular exatamente uma identidade `MEDICO` válida. Edição legada MUST preservar vínculos existentes.

#### Scenario: Cadastro médico novo
- **WHEN** o Administrador salva nome, e-mail e especialidades válidas
- **THEN** o sistema persiste profissional, conta MEDICO e associações atomicamente, gerando identificador interno e credencial temporária segura

#### Scenario: E-mail já cadastrado
- **WHEN** o e-mail normalizado pertence a conta de outra role ou Médico já vinculado
- **THEN** o servidor rejeita o cadastro sem alterar registros ou senhas existentes

#### Scenario: Conta Médica disponível
- **WHEN** o e-mail pertence a conta MEDICO sem vínculo
- **THEN** o servidor reutiliza essa identidade sem redefinir a senha e cria associação única

#### Scenario: Falha na associação
- **WHEN** associação ou constraint falha após iniciar o cadastro
- **THEN** nenhuma identidade órfã ou profissional parcial é persistido

### Requirement: E-mail de onboarding reflete status real
O sistema MUST registrar se um e-mail de boas-vindas foi aceito pelo serviço externo, não enviado, falhou ou está indeterminado. MUST impedir que ausência de credenciais Resend seja apresentada como envio concluído.

#### Scenario: Resend não configurado
- **WHEN** não há configuração válida do Resend no servidor
- **THEN** o cadastro local pode concluir, mas o sistema informa que o e-mail não foi enviado

#### Scenario: Provedor confirma aceitação
- **WHEN** a API Resend aceita a requisição de boas-vindas
- **THEN** o estado registrado indica aceitação pelo provedor, sem afirmar entrega ou leitura

#### Scenario: Erro ou timeout
- **WHEN** o provedor falha ou não fornece confirmação conclusiva
- **THEN** o servidor não expõe segredo e sinaliza falha ou estado indeterminado, sem reenvio cego
