## 1. Modelagem e migração

- [ ] 1.1 Definir enums fechados de prioridade e estado da fila, sem reutilizar estados de Consulta.
- [ ] 1.2 Criar modelos persistentes mínimos de `Patient` e `QueueEntry`, com constraints, índices e FK para o Médico autenticado quando aplicável.
- [ ] 1.3 Implementar normalização e validação server-side de CPF, incluindo dígitos verificadores e rejeição de duplicidade.
- [ ] 1.4 Gerar nova migração Alembic sobre a revisão de autenticação, revisar `upgrade`/`downgrade` e validar em PostgreSQL descartável.

## 2. Serviços de paciente e fila

- [ ] 2.1 Implementar serviço de cadastro e busca de paciente sem expor CPF ou payloads sensíveis em logs/erros.
- [ ] 2.2 Implementar criação de entrada `AGUARDANDO` com sintomas, prioridade válida e timestamp gerado no servidor.
- [ ] 2.3 Implementar consulta ordenada da fila por prioridade, `entered_at` e id.
- [ ] 2.4 Implementar reavaliação manual somente de entradas `AGUARDANDO`.
- [ ] 2.5 Implementar retirada lógica da fila com motivo e timestamp, sem exclusão física.
- [ ] 2.6 Implementar chamada atômica do próximo paciente com lock no PostgreSQL e associação ao Médico autenticado.
- [ ] 2.7 Implementar finalização somente pelo Médico responsável pela entrada em atendimento.

## 3. Autorização e States Reflex

- [ ] 3.1 Criar State/serviços da Recepção revalidando role `RECEPCIONISTA` em cada leitura e mutação protegida.
- [ ] 3.2 Criar State/serviços do Médico revalidando role `MEDICO` em chamada, leitura do atendimento ativo e finalização.
- [ ] 3.3 Garantir que sessão inválida/expirada e role incompatível não retornem dados da fila nem alterem registros.
- [ ] 3.4 Garantir que erros de validação e concorrência sejam convertidos em feedback genérico e seguro para a interface.

## 4. Interface da Recepção

- [ ] 4.1 Substituir o placeholder de `/recepcao` por layout responsivo do fluxo de paciente/fila preservando header e logout existentes.
- [ ] 4.2 Criar formulário acessível de paciente com labels, validação, estado de envio e feedback de CPF inválido/duplicado.
- [ ] 4.3 Criar formulário acessível de entrada na fila com sintomas e prioridade explícita, sem linguagem que sugira classificação automática.
- [ ] 4.4 Exibir fila ativa na ordem do servidor com prioridade, horário e ações permitidas.
- [ ] 4.5 Implementar fluxos de reavaliação e retirada com confirmação adequada e estados de sucesso/erro/vazio/loading.

## 5. Interface do Médico

- [ ] 5.1 Substituir o placeholder de `/medico` por painel responsivo de chamada e atendimento ativo.
- [ ] 5.2 Implementar ação "Chamar próximo" com prevenção de disparos duplicados e feedback para fila vazia.
- [ ] 5.3 Exibir somente o atendimento ativo associado ao Médico autenticado e permitir sua finalização.
- [ ] 5.4 Garantir navegação por teclado, foco visível, contraste e mensagens acessíveis nos estados da fila.

## 6. Testes e validação

- [ ] 6.1 Testar CPF válido, CPF inválido, normalização e duplicidade.
- [ ] 6.2 Testar ordenação `VERMELHO > AMARELO > VERDE`, desempate por horário/id e ausência de escalonamento automático.
- [ ] 6.3 Testar reavaliação, retirada e transições inválidas.
- [ ] 6.4 Testar autorização de Recepcionista e Médico, inclusive chamadas diretas com role incompatível.
- [ ] 6.5 Testar duas chamadas concorrentes em PostgreSQL garantindo que uma entrada não seja atribuída a dois Médicos.
- [ ] 6.6 Executar migração em PostgreSQL descartável, suíte completa e `reflex compile --dry`, corrigindo regressões antes de concluir a change.
