## ADDED Requirements

### Requirement: Gerenciamento autorizado de convites do portal
O gerenciamento de acesso MUST consultar o vínculo real da conta e o histórico persistido de convites, exigir consentimento explícito em cada solicitação e revalidar a autorização server-side. Convites MUST NOT duplicar conta ou expor código, hash ou senha.

#### Scenario: Consulta de situação do portal
- **WHEN** uma recepcionista autorizada abre o gerenciamento de acesso
- **THEN** a interface consulta a situação persistida e mostra o estado compatível, sem equiparar e-mail cadastrado a conta ativa

#### Scenario: Convite válido
- **WHEN** a recepcionista informa e-mail válido, confirma consentimento e solicita convite de paciente sem conta
- **THEN** o serviço aplica autorização e deduplicação e registra a tentativa; confirmação do provedor é comunicada somente como aceitação, não entrega

#### Scenario: Consentimento ausente ou e-mail já utilizado
- **WHEN** o consentimento não é confirmado ou o e-mail já pertence a outra conta/convite ativo
- **THEN** o servidor recusa a operação sem criar outra conta ou enviar mensagem

#### Scenario: Reenvio antecipado
- **WHEN** um convite ao mesmo paciente é solicitado antes de transcorrer 2 minutos
- **THEN** o serviço bloqueia novo convite e preserva o histórico e o vínculo

#### Scenario: Falha de envio ou acesso negado
- **WHEN** o provedor não aceita a mensagem ou a sessão não tem permissão
- **THEN** o sistema apresenta resultado fiel ou bloqueia a ação sem ativar acesso nem expor token
