## ADDED Requirements

### Requirement: Ficha administrativa de funcionário persistido
O sistema MUST apresentar `/admin/funcionarios/[employee_id]` como consulta administrativa permanente e MUST projetar somente dados reais de funcionário autorizados no servidor. A interface MUST distinguir carregamento, registro não encontrado e falha recuperável, sem mostrar outro funcionário durante a navegação.

#### Scenario: Administrador consulta funcionário existente
- **WHEN** Administrador com sessão válida abre a ficha de um Médico ou Recepcionista cadastrado
- **THEN** a ficha mostra nome quando disponível, e-mail secundário, perfil em badge compacto e somente dados profissionais vinculados existentes, sem mensagem permanente de cadastro concluído

#### Scenario: Cadastro antigo sem nome
- **WHEN** a conta não possui nome persistido nem vínculo profissional com nome
- **THEN** a ficha indica “Nome não informado” e não trata o e-mail como nome fictício

#### Scenario: Registro inválido ou inexistente
- **WHEN** o identificador da rota não corresponde a funcionário elegível
- **THEN** a ficha apresenta estado de não encontrado e caminho de retorno à listagem

#### Scenario: Falha ao consultar funcionário
- **WHEN** a leitura autorizada falha por motivo operacional
- **THEN** o sistema limpa a projeção anterior, apresenta mensagem segura e oferece nova tentativa

#### Scenario: Sessão ausente ou role não autorizada
- **WHEN** alguém sem sessão válida ou com role diferente de Administrador tenta consultar a ficha diretamente
- **THEN** o servidor rejeita a consulta sem devolver dados de funcionário e a interface não libera o conteúdo protegido
