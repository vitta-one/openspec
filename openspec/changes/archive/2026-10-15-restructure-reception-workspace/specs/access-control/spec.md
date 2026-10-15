## ADDED Requirements

### Requirement: Subrotas operacionais de Recepção seguem autorização por rota
O sistema MUST restringir o dashboard e as subrotas de Agenda, Pacientes e Fila à role RECEPCIONISTA, validando sessão e role no servidor antes de expor qualquer dado.

#### Scenario: Sessão válida
- **WHEN** Recepcionista acessa diretamente cada rota
- **THEN** o servidor valida sua sessão e apresenta apenas dados e ações da Recepção

#### Scenario: Perfil sem permissão
- **WHEN** outra role acessa uma rota da Recepção
- **THEN** o servidor impede a leitura e redireciona a acesso negado

#### Scenario: Sessão expirada
- **WHEN** uma atualização é solicitada sem sessão válida
- **THEN** o sistema limpa os dados protegidos e direciona para login
