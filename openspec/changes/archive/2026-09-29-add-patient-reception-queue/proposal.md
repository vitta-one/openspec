## Why

A fundação de autenticação e RBAC já permite identificar com segurança Recepcionistas e Médicos, mas os painéis ainda não executam um fluxo operacional real. O próximo incremento do Vitta-One precisa permitir registrar um paciente e controlar sua passagem por uma fila de atendimento de forma simples, rastreável e compatível com a prioridade informada pela triagem externa.

Esta change implementa o primeiro fluxo funcional do produto sem antecipar agendamento, prontuário longitudinal ou decisões clínicas automatizadas.

## What Changes

- Permitir que a Recepcionista cadastre e localize pacientes por dados mínimos, com CPF normalizado e único.
- Permitir que a Recepcionista registre uma entrada na fila com sintomas informados, prioridade e horário de entrada.
- Representar a prioridade exclusivamente como `VERMELHO`, `AMARELO` ou `VERDE`, informada pela operação; o sistema não calcula gravidade clínica.
- Ordenar a fila por prioridade `VERMELHO > AMARELO > VERDE` e, dentro da mesma prioridade, pelo horário de entrada.
- Permitir reavaliação manual de sintomas/prioridade enquanto o paciente aguarda, recalculando a posição naturalmente.
- Permitir retirar da fila pacientes que desistiram, não compareceram ou não devem mais aguardar, mantendo o registro histórico em vez de apagar dados.
- Permitir que um Médico chame atomicamente o próximo paciente elegível da fila e finalize o atendimento operacional.
- Tornar os painéis existentes de Recepção e Médico funcionais para esse fluxo, mantendo autorização server-side e tratamento responsivo/acessível.
- Não aumentar automaticamente a prioridade com o tempo de espera.

## Capabilities

### New Capabilities

- `patient-reception-queue`: cadastro mínimo de paciente, entrada e manutenção da fila, ordenação por prioridade, chamada do próximo paciente e finalização operacional.

### Modified Capabilities

- `access-control`: os destinos protegidos por role deixam de ser somente shells vazios e passam a poder hospedar funcionalidades autorizadas por capabilities específicas.

## Out of Scope

- triagem clínica dentro do sistema ou cálculo automático de gravidade;
- diagnóstico, anamnese, prontuário longitudinal ou registro clínico completo;
- prescrições, assinatura ZapSign e envio de documentos;
- exames e Cloudinary;
- agendamento, agenda e regras de consulta previamente planejadas;
- pagamento ou Asaas;
- painel público de senhas/pacientes;
- roteamento automático por especialidade ou regras de disponibilidade de profissionais;
- relatórios gerenciais e métricas;
- escalonamento automático de prioridade por tempo de espera.

## Impact

- Introduz modelos persistentes de Paciente e Entrada de Fila no PostgreSQL.
- Introduz um ciclo operacional próprio da fila, separado do ciclo futuro de Consulta.
- Substitui o conteúdo placeholder dos painéis de Recepção e Médico por interfaces funcionais do fluxo desta change.
- Reutiliza a sessão e o RBAC existentes; nenhuma nova role é adicionada.
- Exige uma nova migração Alembic e testes de ordenação, autorização, transições e concorrência de chamada do próximo paciente.
