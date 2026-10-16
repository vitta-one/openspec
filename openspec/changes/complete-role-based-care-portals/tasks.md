## 1. Persistência e acesso

- [x] 1.1 Adicionar role PACIENTE e migration reversível para constraint, vínculo e convites.
- [x] 1.2 Criar serviço de convite/ativação de uso único com segredo somente em hash.
- [x] 1.3 Criar endpoint POST de ativação sem Reflex State e sem segredo em URL.
- [x] 1.4 Registrar trilha de reagendamento na transação existente.

## 2. Médico e paciente

- [x] 2.1 Criar boundaries de agenda/pacientes do médico derivadas do profissional autenticado.
- [x] 2.2 Criar boundary da agenda do paciente derivada do vínculo da sessão.
- [x] 2.3 Criar telas Reflex por período com horário local, status e endereço configurado.
- [x] 2.4 Atualizar shell e redirecionamento por papel.

## 3. Recepção

- [x] 3.1 Permitir atualizar contato operacional do paciente sem alterar CPF ou vínculo.
- [x] 3.2 Permitir convite e reenvio somente após consentimento explícito.
- [x] 3.3 Exibir estado de entrega sem expor código, token ou dado clínico.

## 4. Verificação

- [x] 4.1 Testar isolamento de agenda, vínculo de conta, consentimento e uso único.
- [x] 4.2 Testar histórico de reagendamento e fuso configurado.
- [x] 4.3 Validar migration em SQLite descartável, estrutura OpenSpec e Reflex compile sem navegador.

## Nota de validação

A estrutura e os cenários OpenSpec foram verificados localmente. O validador oficial via npm não foi executado: o auto-review bloqueou a chamada ao pacote porque ele tentaria contatar `edge.openspec.dev` e poderia enviar metadados do repositório.
