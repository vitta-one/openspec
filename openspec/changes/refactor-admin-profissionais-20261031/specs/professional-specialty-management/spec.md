## MODIFIED Requirements

### Requirement: Administrador gerencia profissionais
O sistema MUST permitir cadastrar profissional com nome e e-mail único, com zero ou mais especialidades válidas, sem pedir identificador interno nem vínculo manual de conta. MUST gerar identificador interno único, sem simular CRM, e vincular exatamente uma identidade `MEDICO` válida no fluxo de cadastro médico. Edição legada MUST preservar vínculos existentes quando não alterados.

#### Scenario: Novo profissional válido
- **WHEN** um Administrador autenticado informa nome e e-mail válido, com zero ou mais especialidades ativas
- **THEN** o sistema cria exatamente um profissional ativo e a identidade Médica vinculada sem exigir identificador interno

#### Scenario: Identificador profissional duplicado
- **WHEN** a operação legada de domínio tenta cadastrar ou editar profissional com identificador interno já atribuído
- **THEN** o servidor rejeita a duplicidade sem alterar registros existentes

#### Scenario: Profissional sem especialidade
- **WHEN** o Administrador salva um novo médico sem selecionar especialidades
- **THEN** o cadastro e o vínculo único com a identidade Médica são persistidos sem associação de especialidade

#### Scenario: Especialidades removidas na edição
- **WHEN** o Administrador desmarca todas as especialidades de um profissional existente
- **THEN** o sistema remove os vínculos válidos sem apagar o profissional ou alterar sua identidade de login

#### Scenario: Cadastro médico novo
- **WHEN** o Administrador salva nome, e-mail e especialidades opcionais válidas
- **THEN** o sistema persiste profissional, conta MEDICO e associações atomicamente, gerando identificador interno e credencial temporária segura

#### Scenario: E-mail já cadastrado
- **WHEN** o e-mail normalizado pertence a conta de outra role ou Médico já vinculado
- **THEN** o servidor rejeita o cadastro sem alterar registros ou senhas existentes

#### Scenario: Conta Médica disponível
- **WHEN** o e-mail pertence a conta MEDICO sem vínculo
- **THEN** o servidor reutiliza essa identidade sem redefinir senha e cria associação única

#### Scenario: Falha na associação
- **WHEN** uma associação ou constraint falha durante o cadastro
- **THEN** nenhuma identidade órfã ou profissional parcial é persistido

## ADDED Requirements

### Requirement: Diretório completo de profissionais oferece tabela compacta e ações protegidas
O sistema MUST exibir os profissionais autorizados em tabela semântica com nome, e-mail, especialidades, situação profissional, acesso e ações, preservando operações acessíveis em mobile e diálogos existentes.

#### Scenario: Especialidades vinculadas
- **WHEN** um profissional possui múltiplas especialidades
- **THEN** o diretório mostra um resumo compacto e oferece consulta acessível aos vínculos persistidos

#### Scenario: Sem especialidade
- **WHEN** um profissional não possui especialidade vinculada
- **THEN** o diretório apresenta “Não vinculada”, sem dados inventados

#### Scenario: Busca e filtros combinados
- **WHEN** o Administrador pesquisa nome ou e-mail e seleciona filtros de situação e especialidade
- **THEN** a lista combina os critérios, mostra quantidade encontrada e reinicia a paginação

#### Scenario: Resultado vazio
- **WHEN** não existem profissionais compatíveis com a seleção
- **THEN** a página apresenta mensagem adequada e controle de limpeza dos filtros

#### Scenario: Editar em contexto
- **WHEN** o Administrador seleciona Editar em uma linha
- **THEN** o modal existente abre preenchido e salva mediante autorização e validação no servidor

#### Scenario: Confirmar alteração de situação
- **WHEN** o Administrador solicita desativação ou reativação
- **THEN** um diálogo identifica o profissional e exige confirmação antes da mutação

#### Scenario: Situação alterada em outra sessão
- **WHEN** o status persistido mudou desde a confirmação exibida
- **THEN** o servidor recusa a operação obsoleta, preserva o estado atual e apresenta feedback

#### Scenario: Conta distinta da situação profissional
- **WHEN** um profissional é desativado
- **THEN** seus vínculos são preservados e o sistema não altera automaticamente a conta de login

### Requirement: Estados de acesso e reemissão são apresentados com precisão
O sistema MUST diferenciar a situação operacional da situação de envio da credencial inicial. Uma requisição aceita pelo provedor MUST ser exibida apenas como aceita, nunca como entregue ao destinatário.

#### Scenario: Envio não configurado
- **WHEN** o estado persistido é `NOT_CONFIGURED`
- **THEN** o diretório informa que não foi enviado e oferece reemissão controlada quando elegível

#### Scenario: Falha ou estado indeterminado
- **WHEN** o estado persistido é `FAILED` ou `UNKNOWN`
- **THEN** o diretório não informa sucesso e exige confirmação explícita para gerar novo acesso

#### Scenario: Exceção de transporte na reemissão
- **WHEN** a chamada ao provedor falha sem confirmação de aceite
- **THEN** o sistema não repete automaticamente o envio nem afirma entrega

#### Scenario: Acesso não elegível para reemissão
- **WHEN** o profissional não tem conta elegível ou o onboarding já está concluído
- **THEN** o sistema não mostra uma ação de reemissão indevida
