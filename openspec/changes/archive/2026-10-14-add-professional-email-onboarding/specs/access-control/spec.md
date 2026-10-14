## ADDED Requirements

### Requirement: Senha inicial temporária impede acesso clínico antes de troca
O sistema MUST exigir troca de senha inicial temporária no primeiro login; MUST aplicar expiração da credencial, validar a senha nova e bloquear operações protegidas enquanto a troca não estiver concluída.

#### Scenario: Login com senha inicial válida
- **WHEN** Médico apresenta credencial temporária válida dentro do prazo
- **THEN** o servidor cria contexto provisório e direciona somente ao fluxo de troca obrigatória

#### Scenario: Tentativa de acesso direto a operação clínica
- **WHEN** a identidade Médica provisória chama uma operação server-side que exige role MEDICO
- **THEN** o servidor nega a operação sem acessar dados clínicos

#### Scenario: Senha inicial expirada
- **WHEN** Médico tenta autenticar usando senha inicial fora do prazo
- **THEN** a autenticação não libera acesso e comunica necessidade de reemissão administrativa

#### Scenario: Conclusão da troca
- **WHEN** Médico confirma a senha atual e escolhe nova senha válida
- **THEN** o hash é atualizado, o requisito de troca é removido e o acesso normal pode prosseguir
