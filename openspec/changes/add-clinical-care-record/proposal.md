## Why

O Vitta-One já cobre acesso, pacientes, fila, profissionais, agenda e o lifecycle operacional da Consulta até `CONCLUIDA`. O Médico consegue chamar e finalizar o paciente, mas o sistema ainda não possui um registro clínico persistido do que ocorreu durante o atendimento.

A próxima evolução deve transformar o atendimento ativo em um registro clínico simples, rastreável e vinculado à Consulta correta, sem antecipar prescrição, exames, anexos ou integrações externas.

## What Changes

- Criar um registro persistente de **Atendimento clínico** vinculado a uma única `Consultation`, ao mesmo paciente e ao Médico responsável.
- Criar o Atendimento automaticamente quando uma Consulta agendada entra em `EM_ANDAMENTO`, na mesma transação que inicia a fila/Consulta.
- Garantir no banco que uma Consulta possua no máximo um Atendimento clínico.
- Permitir que o Médico responsável edite o Atendimento somente enquanto a Consulta estiver `EM_ANDAMENTO`.
- Registrar quatro áreas simples de texto:
  - queixa principal;
  - anamnese;
  - diagnóstico;
  - conduta e observações.
- Permitir salvamento incremental durante o atendimento; esta change não exige que os quatro campos estejam preenchidos para concluir a Consulta.
- Ao concluir a Consulta, tornar o Atendimento imutável para operações normais.
- Exibir no painel Médico o contexto persistido do paciente já chamado, o formulário do Atendimento atual e o histórico clínico anterior do mesmo paciente.
- Formar o histórico clínico como uma projeção cronológica de Atendimentos de Consultas concluídas, sem criar uma tabela separada de “Prontuário” nesta etapa.
- Paginar o histórico clínico no servidor para evitar carregamento ilimitado.
- Restringir edição ao Médico vinculado ao profissional da Consulta.
- Permitir leitura do histórico somente no contexto de um atendimento ativo do mesmo paciente pelo Médico autenticado.
- Fazer o preview local do Administrador projetar Atendimento/histórico de forma somente leitura, condicionado ao modo local de QA já existente.
- Tratar textos clínicos como dados sensíveis: não registrar conteúdo em logs, mensagens de erro ou telemetria.

## Capabilities

### New Capabilities

- `clinical-care-record`: criação, edição, bloqueio pós-conclusão e projeção cronológica de registros clínicos vinculados a Consultas.

### Modified Capabilities

Nenhuma capability consolidada precisa ter requisitos substituídos. Esta change consome o lifecycle já estabelecido por `consultation-care-lifecycle` e mantém suas transições.

## Scope Decisions

Para manter a entrega simples:

- o Atendimento clínico é criado somente para Consultas agendadas que entram em `EM_ANDAMENTO`;
- walk-ins sem `Consultation` continuam sem Atendimento clínico nesta change;
- existe no máximo um Atendimento por Consulta;
- os campos são texto livre, sem CID/ICD, templates ou estrutura clínica adicional;
- salvar o Atendimento não altera estado de Consulta ou fila;
- concluir a Consulta não depende de preenchimento mínimo dos quatro campos;
- o histórico usa somente registros de Consultas `CONCLUIDA`;
- “Prontuário” continua sendo uma visão/agregação do histórico, não uma entidade física independente.

## Out of Scope

- prescrições e receitas;
- ZapSign;
- exames e anexos;
- Cloudinary;
- CID/ICD, terminologias médicas ou autocomplete clínico;
- assinatura do Atendimento;
- versionamento/auditoria de cada alteração de campo;
- edição pós-conclusão;
- reabertura de Consulta concluída;
- Atendimento clínico para walk-in sem Consulta;
- compartilhamento externo do histórico;
- PDF/relatório clínico;
- e-mail;
- financeiro/Asaas;
- dashboards clínicos.

## Impact

- Adiciona nova entidade persistente de Atendimento clínico.
- Evolui a transição de início de Consulta para criar o Atendimento na mesma transação.
- Evolui o painel Médico com formulário clínico simples e histórico paginado.
- Evolui o preview local do Administrador para substituir o placeholder de prontuário por dados reais somente leitura.
- Introduz migration incremental sobre a revisão atual de lifecycle.
- Exige testes de autorização, imutabilidade pós-conclusão, atomicidade e concorrência PostgreSQL.
