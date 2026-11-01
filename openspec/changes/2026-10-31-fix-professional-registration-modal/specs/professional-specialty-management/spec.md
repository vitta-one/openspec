## MODIFIED Requirements

### Requirement: Administrador gerencia profissionais
O sistema MUST permitir cadastrar profissional com nome, e-mail único e zero, uma ou várias especialidades ativas, sem pedir identificador interno nem vínculo manual de conta. MUST gerar identificador interno único, sem simular CRM, e vincular exatamente uma identidade `MEDICO` válida. Edição legada MUST preservar vínculos existentes, salvo remoção explícita das associações.

#### Scenario: Novo profissional válido
- **WHEN** um Administrador autenticado informa nome e e-mail profissional válido e, opcionalmente, especialidades ativas
- **THEN** o sistema cria exatamente um profissional ativo e identidade Médica vinculada, com as associações selecionadas e sem exigir identificador interno

#### Scenario: Identificador profissional duplicado
- **WHEN** a operação legada de domínio tenta cadastrar ou editar um profissional com identificador interno já atribuído
- **THEN** o servidor rejeita a duplicidade sem alterar registros existentes; o fluxo simplificado gera identificador interno único

#### Scenario: Profissional sem especialidade
- **WHEN** o Administrador salva um profissional sem especialidades
- **THEN** o servidor persiste o cadastro e a identidade necessária sem criar vínculos de especialidade, permitindo associação posterior

#### Scenario: Cadastro médico novo
- **WHEN** o Administrador salva nome, e-mail e especialidades válidas, caso selecionadas
- **THEN** o sistema persiste profissional, conta MEDICO e associações existentes atomicamente, gerando identificador interno e credencial temporária segura quando necessária

#### Scenario: E-mail já cadastrado
- **WHEN** o e-mail normalizado pertence a conta de outra role ou Médico já vinculado
- **THEN** o servidor rejeita o cadastro sem alterar registros ou senhas existentes

#### Scenario: Conta Médica disponível
- **WHEN** o e-mail pertence a conta MEDICO sem vínculo
- **THEN** o servidor reutiliza essa identidade sem redefinir a senha e cria associação única

#### Scenario: Falha na associação
- **WHEN** associação ou constraint falha após iniciar o cadastro
- **THEN** nenhuma identidade órfã ou profissional parcial é persistido

### Requirement: Relação entre profissionais e especialidades é muitos-para-muitos
O sistema MUST permitir que um profissional esteja associado a zero, uma ou várias especialidades e MUST permitir que uma especialidade esteja associada a vários profissionais.

#### Scenario: Profissional com múltiplas especialidades
- **WHEN** o Administrador seleciona duas ou mais especialidades ativas para um profissional
- **THEN** todas as associações são persistidas sem duplicidade

#### Scenario: Especialidade compartilhada
- **WHEN** dois profissionais diferentes são associados à mesma especialidade ativa
- **THEN** ambas as associações são aceitas e permanecem independentes

#### Scenario: Associação duplicada
- **WHEN** a mesma especialidade é enviada mais de uma vez para o mesmo profissional
- **THEN** o sistema mantém no máximo uma associação persistida para esse par

#### Scenario: Remover todas as especialidades
- **WHEN** um Administrador edita profissional e desmarca todas as especialidades
- **THEN** o profissional permanece válido e sem vínculos de especialidade

## ADDED Requirements

### Requirement: Cadastro médico administrativo mantém um único fluxo acessível
As entradas de cadastro médico em Funcionários e Profissionais MUST reutilizar o mesmo State, formulários, serviços e regras de domínio. O modal de Profissionais MUST possuir título acessível, ação de fechamento, rótulos de campo, erros junto aos campos de identificação e especialidades opcionais com controle nativo, foco visível e navegação por teclado. O estado de envio de e-mail MUST refletir apenas o resultado efetivamente conhecido do provedor.

#### Scenario: Modal sem especialidades disponíveis
- **WHEN** o Administrador abre Novo profissional sem especialidades ativas disponíveis
- **THEN** o modal informa a ausência de opções e permite cadastrar sem vínculo

#### Scenario: Erro de nome ou e-mail
- **WHEN** o Administrador submete nome vazio, somente espaços ou e-mail inválido
- **THEN** o modal mantém valores corrigíveis e apresenta erro associado ao respectivo campo sem persistir registros

#### Scenario: Cancelamento e teclado
- **WHEN** o Administrador aciona Cancelar, o botão de fechar ou Escape sem submissão em andamento
- **THEN** o modal é fechado sem mutações, o foco retorna ao contexto de origem e a página principal torna-se interativa

#### Scenario: Sucesso e feedback real de e-mail
- **WHEN** o cadastro persiste, mas o provedor de e-mail não está configurado
- **THEN** a interface confirma o cadastro sem afirmar entrega de instruções

#### Scenario: Consistência entre entradas
- **WHEN** o cadastro médico é iniciado a partir de Funcionários ou Profissionais
- **THEN** as duas entradas submetem a mesma regra de unicidade, RBAC, validação e persistência, sem duplicações; o diretório reflete os dados reais
