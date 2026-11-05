## ADDED Requirements

### Requirement: Administração persiste dados institucionais
O sistema MUST permitir a um Administrador autenticado consultar e salvar nome (máximo 160 caracteres) e endereço (máximo 500 caracteres) da clínica em PostgreSQL, sem editar variáveis de ambiente.

#### Scenario: Primeiro salvamento
- **WHEN** o Administrador fornece nome e endereço válidos e salva
- **THEN** o servidor cria uma única configuração e exibe a confirmação de sucesso apenas após commit

#### Scenario: Alteração posterior
- **WHEN** o Administrador atualiza os dados e abre novamente a página
- **THEN** os valores persistidos são exibidos, inclusive após reinicialização da aplicação

#### Scenario: Campo obrigatório inválido
- **WHEN** o nome ou endereço é vazio, contém apenas espaços, excede o limite ou contém controles inválidos
- **THEN** o servidor rejeita a atualização, a interface apresenta erro no campo e preserva o texto do usuário

### Requirement: Controle de acesso e integridade na edição
O servidor MUST validar sessão, role e versão esperada antes de cada mudança e MUST impedir mais de uma configuração para a clínica única.

#### Scenario: Perfil não autorizado
- **WHEN** Recepcionista, Médico, Financeiro, Paciente ou sessão inválida tenta salvar
- **THEN** a operação é negada sem gravar alteração

#### Scenario: Submissão repetida
- **WHEN** uma operação idêntica é repetida
- **THEN** a configuração e a auditoria não recebem duplicação

#### Scenario: Alteração concorrente
- **WHEN** outro Administrador já atualizou uma revisão
- **THEN** a atualização antiga é rejeitada com feedback de conflito e sem sobrescrever os dados recentes

### Requirement: Auditoria transacional
O sistema MUST registrar o autor, os dados anteriores e os novos dados de cada mudança real na mesma transação da configuração.

#### Scenario: Gravação concluída
- **WHEN** nome ou endereço é modificado com sucesso
- **THEN** um evento histórico identifica alteração, valores e autor

### Requirement: Status e interface de configuração
A página MUST indicar se há configuração persistida, apresentar carregamento/salvamento, erros acessíveis e ação real de salvar.

#### Scenario: Configuração não persistida
- **WHEN** ainda não há registro no banco
- **THEN** o formulário pode apresentar valores legados válidos ou campos vazios e orienta o Administrador a salvar

#### Scenario: Falha no salvamento
- **WHEN** a transação falha
- **THEN** não aparece sucesso; os campos permanecem para nova tentativa
