## MODIFIED Requirements

### Requirement: Endereço verdadeiro da clínica
O sistema MUST exibir nome/endereço institucionais reais do PostgreSQL nas próximas leituras do portal, com fallback opcional para configuração válida de implantação somente quando não há dado persistido.

#### Scenario: Endereço ausente
- **WHEN** nome/endereço não estão persistidos nem existem valores legados válidos
- **THEN** a UI informa que a Administração ainda precisa configurar o local e não mostra endereço de exemplo

#### Scenario: Administração atualiza o endereço
- **WHEN** o Administrador salva dados válidos no banco
- **THEN** o portal exibe os dados atualizados na próxima leitura sem reinício da aplicação e sem substituir o logotipo Vitta One
