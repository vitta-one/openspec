## Purpose

Permitir que o Médico responsável crie Prescrições estruturadas durante uma Consulta em andamento, mantenha múltiplos itens/documentos, consulte Prescrições concluídas no histórico e use uma visualização protegida pronta para impressão sem antecipar assinatura digital.

## ADDED Requirements

### Requirement: Prescrição pertence ao Atendimento clínico e à Consulta
O sistema MUST vincular cada Prescription a um ClinicalCareRecord existente, à mesma Consultation e ao Médico responsável pelo Atendimento.

#### Scenario: Contexto válido
- **WHEN** o Médico responsável cria uma Prescrição durante uma Consulta `EM_ANDAMENTO`
- **THEN** o Prescription é persistido com `clinical_care_record_id`, `consultation_id` e `doctor_user_id` coerentes com o Atendimento atual

#### Scenario: ClinicalCareRecord e Consultation divergem
- **WHEN** os vínculos informados não representam o mesmo Atendimento
- **THEN** o servidor rejeita a operação sem persistir Prescrição

### Requirement: Um Atendimento pode possuir múltiplas Prescrições
O sistema MUST permitir zero, uma ou várias Prescrições no mesmo ClinicalCareRecord.

#### Scenario: Médico cria segunda Prescrição
- **WHEN** já existe uma Prescrição no Atendimento e a Consulta continua `EM_ANDAMENTO`
- **THEN** o Médico pode criar outro documento independente

### Requirement: Prescrição nasce com um primeiro item válido
O sistema MUST criar Prescription e seu primeiro PrescriptionItem na mesma transação e MUST NOT persistir uma nova Prescrição vazia.

#### Scenario: Primeiro item válido
- **WHEN** o Médico informa medicamento/item e orientação/posologia válidos
- **THEN** Prescription e primeiro item são persistidos atomicamente

#### Scenario: Primeiro item inválido
- **WHEN** medicamento/item ou orientação/posologia está vazio ou excede o limite
- **THEN** o servidor rejeita a operação e nenhuma Prescription é criada

#### Scenario: Persistência do item falha
- **WHEN** a criação do item falha depois da criação lógica do documento
- **THEN** a transação é revertida e nenhuma Prescription vazia permanece

### Requirement: Item de Prescrição possui conteúdo simples e limitado
Cada PrescriptionItem MUST possuir medicamento/item e orientação/posologia obrigatórios e observações opcionais.

#### Scenario: Item válido
- **WHEN** medicamento/item possui até 300 caracteres, orientação/posologia até 2.000 e observações até 2.000
- **THEN** o item pode ser persistido

#### Scenario: Campo excede limite
- **WHEN** qualquer campo excede seu limite
- **THEN** o servidor rejeita a mutação, preserva o valor anterior e informa o campo sem ecoar conteúdo prescrito

### Requirement: Observações gerais da Prescrição são opcionais
O sistema MUST permitir `general_notes` vazio ou com até 4.000 caracteres.

#### Scenario: Médico altera observações gerais
- **WHEN** a Consulta está `EM_ANDAMENTO` e o Médico responsável salva observações válidas
- **THEN** somente o Prescription correspondente e seu `updated_at` são atualizados

### Requirement: Somente o Médico responsável pode modificar Prescrições
O sistema MUST restringir criação, edição e exclusão à conta Médica responsável pelo Atendimento e pela Consultation.

#### Scenario: Médico responsável altera
- **WHEN** ownership e estado são válidos
- **THEN** a mutação pode prosseguir

#### Scenario: Outro Médico tenta alterar
- **WHEN** outra identidade Médica chama diretamente a operação
- **THEN** o servidor rejeita sem retornar o conteúdo prescrito

#### Scenario: Role não Médica tenta alterar
- **WHEN** Recepcionista, Financeiro ou Administrador normal chama a operação
- **THEN** o servidor rejeita antes de ler ou alterar dados protegidos

### Requirement: Prescrições só são mutáveis durante Consulta Em andamento
O sistema MUST aceitar mutações somente quando a Consultation relacionada estiver `EM_ANDAMENTO`.

#### Scenario: Consulta concluída
- **WHEN** há tentativa de editar/adicionar/remover/excluir após `CONCLUIDA`
- **THEN** o servidor rejeita e preserva o histórico

#### Scenario: Consulta confirmada ainda aguardando
- **WHEN** há tentativa de criar Prescrição antes do atendimento iniciar
- **THEN** o servidor rejeita

#### Scenario: Consulta cancelada
- **WHEN** há tentativa de mutação em Consulta cancelada
- **THEN** o servidor rejeita

### Requirement: Médico pode adicionar itens a uma Prescrição editável
O sistema MUST permitir adicionar PrescriptionItem válido a Prescription do Atendimento atual.

#### Scenario: Novo item
- **WHEN** o Médico responsável adiciona um item válido
- **THEN** o item é persistido e aparece ao final da lista do documento

### Requirement: Médico pode editar item existente
O sistema MUST permitir editar medicamento/item, orientação/posologia e observações de um item durante `EM_ANDAMENTO`.

#### Scenario: Edição válida
- **WHEN** o item pertence à Prescrição autorizada e os campos são válidos
- **THEN** o item e seu `updated_at` são atualizados

#### Scenario: Item de outra Prescrição
- **WHEN** o identificador do item não pertence ao documento/contexto autorizado
- **THEN** a operação é rejeitada

### Requirement: Toda Prescrição persistida mantém ao menos um item
O sistema MUST impedir remoção isolada quando o item alvo é o único item da Prescription.

#### Scenario: Remover item intermediário
- **WHEN** a Prescrição possui dois ou mais itens
- **THEN** o Médico pode remover um deles durante `EM_ANDAMENTO`

#### Scenario: Remover único item
- **WHEN** a Prescrição possui apenas um item
- **THEN** a operação é rejeitada e a UI orienta a excluir a Prescrição inteira se necessário

### Requirement: Médico pode excluir Prescrição durante atendimento
O sistema MUST permitir excluir uma Prescription inteira somente durante `EM_ANDAMENTO`, removendo seus itens filhos no mesmo fluxo.

#### Scenario: Excluir documento editável
- **WHEN** o Médico responsável confirma exclusão durante `EM_ANDAMENTO`
- **THEN** Prescription e seus PrescriptionItems são removidos e os demais registros do Atendimento permanecem intactos

#### Scenario: Excluir documento concluído
- **WHEN** a Consultation já está `CONCLUIDA`
- **THEN** a exclusão é rejeitada

### Requirement: Mutações de Prescrição não alteram o lifecycle da Consulta
Criar, editar ou remover Prescrição/itens MUST NOT alterar estado ou timestamps de Consultation, QueueEntry ou ClinicalCareRecord.

#### Scenario: Médico salva item
- **WHEN** uma mutação de Prescrição é concluída
- **THEN** somente Prescription/PrescriptionItem e seus timestamps próprios são alterados

### Requirement: Histórico clínico inclui Prescrições de Consultas concluídas
A projeção de histórico clínico MUST incluir as Prescrições pertencentes ao ClinicalCareRecord de cada Consultation `CONCLUIDA`.

#### Scenario: Atendimento anterior possui Prescrições
- **WHEN** o Médico carrega histórico autorizado do paciente
- **THEN** cada item de histórico inclui as Prescrições concluídas e seus itens em ordem de criação

#### Scenario: Atendimento concluído sem Prescrição
- **WHEN** não existem Prescrições para o ClinicalCareRecord
- **THEN** o histórico apresenta estado “Sem prescrições” sem inventar documentos

#### Scenario: Consulta atual está Em andamento
- **WHEN** a Consulta atual ainda não foi concluída
- **THEN** suas Prescrições não aparecem no histórico anterior; aparecem somente na seção editável atual

### Requirement: Histórico de Prescrições usa carregamento limitado à página atual
O sistema MUST carregar Prescrições somente para os ClinicalCareRecords retornados na página atual do histórico.

#### Scenario: Histórico paginado
- **WHEN** a página possui até 10 Atendimentos
- **THEN** a aplicação busca Prescrições apenas desses Atendimentos, evitando carregamento ilimitado do histórico inteiro

### Requirement: Painel Médico possui seção Prescrições simples
A UI MUST exibir Prescrições do Atendimento ativo em seção própria, sem substituir o formulário ClinicalCareRecord.

#### Scenario: Consulta agendada ativa
- **WHEN** existe Atendimento clínico ativo autorizado
- **THEN** o Médico visualiza “Nova prescrição”, documentos existentes, itens e ações compatíveis

#### Scenario: Sem Prescrição
- **WHEN** o Atendimento ainda não possui Prescription
- **THEN** a UI mostra estado vazio honesto e a ação “Nova prescrição”

#### Scenario: Walk-in
- **WHEN** o atendimento ativo não possui Consultation/ClinicalCareRecord
- **THEN** a seção Prescrições desta capability não é exibida

### Requirement: Criação e edição usam dialogs acessíveis
A UI MUST usar dialogs controlados para criar Prescrição, adicionar/editar item e confirmar exclusão do documento.

#### Scenario: Nova Prescrição em viewport estreita
- **WHEN** o Médico abre o dialog em tela estreita
- **THEN** labels, campos e ações permanecem legíveis em uma coluna e sem rolagem horizontal obrigatória

#### Scenario: Exclusão
- **WHEN** o Médico escolhe excluir Prescrição
- **THEN** uma confirmação explícita é exibida sem depender de diálogo nativo do navegador

### Requirement: Finalização evita conflito com operações de Prescrição em andamento
O fluxo normal de finalizar Atendimento MUST ficar indisponível enquanto uma operação de Prescrição estiver sendo submetida.

#### Scenario: Item está sendo salvo
- **WHEN** uma mutação de Prescrição está em andamento
- **THEN** “Finalizar atendimento” permanece indisponível até a operação terminar

#### Scenario: Nenhuma operação pendente
- **WHEN** não há dirty state clínico nem operação de Prescrição em andamento
- **THEN** a finalização segue o lifecycle existente

### Requirement: Prescrição concluída possui visualização protegida pronta para impressão
O sistema MUST oferecer uma superfície de impressão read-only de Prescription persistida.

#### Scenario: Médico autor abre Prescrição ativa
- **WHEN** o Médico responsável acessa uma Prescription do próprio Atendimento
- **THEN** a visualização apresenta os dados persistidos em layout imprimível

#### Scenario: Médico autor reabre Prescrição concluída
- **WHEN** a Consultation está `CONCLUIDA` e o usuário autenticado é o Médico autor
- **THEN** a visualização continua disponível em modo somente leitura

#### Scenario: Outro Médico tenta acessar URL direta
- **WHEN** uma identidade Médica diferente solicita a Prescription por id
- **THEN** o servidor rejeita sem retornar paciente, itens ou observações

#### Scenario: Usuário não autenticado
- **WHEN** não existe sessão válida
- **THEN** o acesso ao conteúdo imprimível é negado/redirecionado conforme contrato de autenticação

### Requirement: Visualização de impressão não implica assinatura digital
A versão imprimível MUST informar claramente que não possui assinatura digital nesta etapa e MUST NOT apresentar indicadores de ZapSign/assinatura.

#### Scenario: Renderização imprimível
- **WHEN** a Prescription é exibida para impressão
- **THEN** paciente, profissional, registro profissional, data da Consulta, itens e observações gerais são exibidos junto do aviso “Documento sem assinatura digital nesta etapa.”

### Requirement: Admin QA projeta Prescrições somente em modo local
O Admin preview local MUST poder exibir Prescrições persistidas em modo somente leitura sem criar uma permissão clínica geral para Administrador.

#### Scenario: Admin QA habilitado
- **WHEN** a flag local está ativa e a sessão é Administrador
- **THEN** Atendimento ativo e histórico do paciente podem mostrar Prescrições reais sem ações de mutação

#### Scenario: Admin QA desabilitado
- **WHEN** a flag local não está ativa
- **THEN** Administrador não recebe API geral para listar/editar Prescrições clínicas

### Requirement: Conteúdo de Prescrição é sensível
O sistema MUST NOT registrar medicamento/item, posologia, observações, CPF ou payload completo de Prescrição em logs, exceptions ou telemetria.

#### Scenario: Validação falha
- **WHEN** um campo excede limite ou está vazio
- **THEN** o erro descreve somente campo/regra e não repete o conteúdo enviado

#### Scenario: Persistência falha
- **WHEN** uma operação de banco falha
- **THEN** a resposta não expõe stack trace, nome interno de constraint nem conteúdo prescrito

### Requirement: Concorrência preserva integridade da Prescrição
O sistema MUST usar locking/revalidação em mutações concorrentes e MUST preservar pelo menos um item por Prescription persistida.

#### Scenario: Dois saves concorrentes no mesmo item
- **WHEN** duas requisições autorizadas editam o mesmo PrescriptionItem
- **THEN** as operações são serializadas e o item termina em um estado válido completo

#### Scenario: Remoção e edição concorrentes
- **WHEN** uma operação remove um item enquanto outra tenta editá-lo
- **THEN** no máximo uma alteração válida é persistida e não surge item órfão

#### Scenario: Duas remoções disputam os últimos itens
- **WHEN** operações concorrentes poderiam deixar a Prescription vazia
- **THEN** locking/revalidação garante que uma Prescription persistida continue com pelo menos um item ou que o documento seja removido por operação explícita de exclusão
