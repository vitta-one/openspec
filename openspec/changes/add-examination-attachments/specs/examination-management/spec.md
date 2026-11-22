## ADDED Requirements

### Requirement: Solicitação de exame pertence a episódio clínico autorizado
O sistema MUST permitir ao Médico responsável registrar uma solicitação de exame vinculada a Patient e ClinicalCareRecord elegíveis, revalidando a sessão e a titularidade do episódio no servidor.

#### Scenario: Pedido válido
- **WHEN** o Médico responsável cria solicitação válida durante atendimento elegível
- **THEN** o pedido é persistido com identificação de paciente, Médico e episódio sem gerar Consultation fictícia

#### Scenario: Médico não responsável
- **WHEN** outra identidade tenta solicitar ou ler exame de episódio alheio
- **THEN** a leitura ou escrita é rejeitada sem dados clínicos no erro

### Requirement: Resultado e anexo mantêm vínculo e integridade
O sistema MUST relacionar resultado/anexo ao pedido existente e MUST garantir que metadados persistidos correspondam a objeto de armazenamento autorizado.

#### Scenario: Resultado válido
- **WHEN** usuário habilitado conforme política aprovada registra resultado do pedido
- **THEN** o resultado é associado ao mesmo paciente/episódio e aparece apenas no histórico autorizado

#### Scenario: Anexo órfão ou ausente
- **WHEN** upload ou persistência falha parcialmente
- **THEN** o sistema sinaliza estado recuperável e reconcilia/compensa o objeto sem apresentar conclusão falsa

### Requirement: Upload e download são protegidos
O sistema MUST validar tipo, tamanho, MIME e propriedade de anexos no servidor e MUST armazenar credenciais Cloudinary fora da interface, oferecendo acesso temporário e autorizado.

#### Scenario: Arquivo rejeitado
- **WHEN** arquivo inválido, excessivo ou não permitido é enviado
- **THEN** a operação falha sem gravar metadados como anexo válido

#### Scenario: Consulta por ID forjado
- **WHEN** usuário modifica patient_id, exam_id ou identificador do objeto
- **THEN** o serviço revalida acesso e nega obtenção do arquivo de outro episódio

### Requirement: Auditoria acompanha mutações de exames
O sistema MUST registrar autoria, instante e tipo de evento relevante de pedido, resultado e anexo, sem inserir conteúdo clínico sensível em logs externos.

#### Scenario: Atualização autorizada
- **WHEN** um resultado ou anexo é alterado conforme política aprovada
- **THEN** o histórico de auditoria preserva referência ao autor e transição sem apagar o rastro anterior

### Requirement: Falhas externas não corrompem prontuário
O sistema MUST tratar indisponibilidade, timeout e resposta inesperada do Cloudinary sem transformar falha técnica em resultado clínico concluído.

#### Scenario: Cloudinary indisponível
- **WHEN** upload ou leitura remota falha
- **THEN** a UI apresenta erro recuperável e o atendimento clínico existente permanece íntegro
