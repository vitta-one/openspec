# Design técnico — Cadastro e portal do paciente

## Componentes

- `patient_directory_components.py`: mantém ação Agendar consulta e adiciona os botões Editar cadastro e Acesso ao portal.
- `patient_dialog_components.py`: duas janelas Radix/Reflex compactas, sem subcards, com rótulos, rodapé e feedback inline.
- `patient_queue/state.py`: rascunho independente para nome/telefone, status de diálogo e carregamento do acesso. A consulta/mutação revalida token e `patient_id` da rota.
- `patient_queue/application.py`: mantém a autorização por role para a escrita cadastral.
- `patient_portal/application.py`: lê status/e-mail somente após autenticação e vinculação real.
- `patient_portal/service.py`: checa usuário/e-mail pré-existente, convite ativo em outro paciente e limita reenvio ao mesmo paciente a 2 minutos.

## Persistência e identidade

`Patient`, `User` e `PatientPortalInvitation` permanecem canônicos. Sem novas colunas, tabelas ou migration. A edição só persiste `name` e `phone`, conservando CPF/`user_id`. O código do convite permanece em hash, expira e é de uso único pelos serviços existentes.

## Estados e feedback

Status: sem acesso; convite pendente; enviado; envio indeterminado/falha; expirado; ativo. O texto de sucesso do envio afirma somente aceitação pelo provedor, não entrega. Erros de validação aparecem junto ao campo ou ao formulário, sem descartar o rascunho.

## Autorização e concorrência

Cada evento consulta a sessão atual e aplica autorização no serviço. No State, escrita/convite exigem que o ID da ficha coincida com o paciente selecionado. Submissões concorrentes no mesmo State são bloqueadas por `is_submitting`; a proteção de reenvio fica no domínio e no banco.

## Acessibilidade

Os dialogs nativos Reflex/Radix gerenciam foco, Escape e retorno ao acionador. Labels ligadas por `id/html_for`, feedback `role=alert/status`, botão fechar com nome acessível, viewport fluida e rolagem limitada em mobile.
