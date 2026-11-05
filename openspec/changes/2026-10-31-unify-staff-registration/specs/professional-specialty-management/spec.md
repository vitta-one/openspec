## MODIFIED Requirements

### Requirement: Administrador gerencia profissionais
O sistema MUST permitir cadastrar profissional com nome, e-mail único e zero ou mais especialidades ativas, sem pedir identificador interno nem vínculo manual de conta. MUST gerar identificador interno único, sem simular CRM, e vincular exatamente uma identidade `MEDICO` válida. A edição MUST permitir atualizar os vínculos para uma coleção vazia, preservando dados históricos sem excluir especialidades.

#### Scenario: Novo profissional válido
- **WHEN** o Administrador informa nome e e-mail profissional válido com ou sem especialidades ativas
- **THEN** o sistema cria exatamente um profissional ativo e uma identidade Médica, incluindo somente os vínculos selecionados

#### Scenario: Profissional sem especialidade
- **WHEN** o Administrador cadastra um médico sem selecionar especialidades
- **THEN** a identidade e o profissional são persistidos atomicamente sem vínculos, para associação posterior

#### Scenario: Edição sem especialidade
- **WHEN** o Administrador salva lista vazia na edição de um profissional
- **THEN** os vínculos atuais são removidos e o profissional permanece cadastrado

#### Scenario: Cadastro médico novo
- **WHEN** o Administrador salva nome, e-mail e especialidades ativas válidas
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

#### Scenario: Identificador profissional duplicado
- **WHEN** a operação legada de domínio tenta cadastrar ou editar profissional com identificador já atribuído
- **THEN** o servidor rejeita a duplicidade; o fluxo simplificado gera identificador interno único
