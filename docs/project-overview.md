# Project Overview — Vitta-One

## 1. Visão geral

O **Vitta-One** é um sistema de gerenciamento de clínica médica destinado a centralizar as principais operações de uma clínica em um único ambiente. A aplicação organiza informações e processos relacionados a pacientes, profissionais, agenda, consultas, atendimentos, prontuários, exames, prescrições, pagamentos e informações gerenciais.

## 2. Problema

A clínica pode operar com informações distribuídas entre documentos, controles manuais ou sistemas diferentes. Isso dificulta a organização dos pacientes, o controle da agenda dos profissionais, a prevenção de conflitos de horário, a consulta ao histórico clínico, o acompanhamento das consultas, o registro dos atendimentos, o controle dos pagamentos e a obtenção de uma visão geral da operação.

O Vitta-One busca centralizar essas informações e tornar o fluxo de trabalho mais organizado e rastreável.

## 3. Objetivos

- centralizar pacientes, profissionais, consultas e atendimentos;
- reduzir conflitos de agenda entre profissionais;
- facilitar o acesso ao histórico clínico do paciente;
- acompanhar as consultas ao longo de seu ciclo de vida;
- centralizar registros de atendimento, diagnósticos, prescrições e exames;
- acompanhar pagamentos associados às consultas;
- apresentar informações gerenciais consolidadas em dashboards.

## 4. Usuários

O sistema possui quatro roles previstas:

### Administrador

Responsável pelo gerenciamento geral, incluindo usuários, profissionais, especialidades, configurações e informações administrativas.

### Recepcionista

Responsável pela rotina operacional da clínica, incluindo cadastro e consulta de pacientes, agendamentos, alterações, cancelamentos, consulta da agenda e acompanhamento dos estados das consultas.

### Médico

Responsável pelo atendimento clínico, consulta ao histórico do paciente, registro de atendimento, diagnóstico, prescrições e exames.

### Financeiro

Responsável pelo registro e consulta de pagamentos, acompanhamento de valores e informações financeiras.

O controle de acesso é baseado em roles simples. Cada role possui seu próprio painel dedicado e não há perfis adicionais previstos no escopo atual.

## 5. Escopo inicial

O escopo funcional inclui:

- gestão de usuários;
- gestão de pacientes;
- gestão de profissionais e especialidades;
- agenda e disponibilidade;
- consultas e seu ciclo de vida;
- atendimento médico;
- prontuário e histórico clínico;
- exames e anexos;
- prescrições;
- financeiro;
- dashboards e informações gerenciais.

O fluxo principal do domínio é:

```text
Paciente → Agendamento → Consulta → Atendimento → Prontuário
```

Quando aplicável, uma consulta também pode estar relacionada a um pagamento. Um atendimento pode produzir diagnóstico, prescrição, solicitação ou registro de exame e outras informações clínicas.

## 6. Regras e restrições importantes

- um profissional não deve possuir consultas conflitantes no mesmo horário;
- uma consulta deve relacionar paciente, profissional e data/horário;
- um atendimento deve estar relacionado à consulta e ao paciente correspondentes;
- o prontuário deve apresentar o histórico de atendimentos em ordem cronológica;
- o dashboard consolida dados existentes e não é uma fonte independente de dados de negócio;
- cada role deve visualizar apenas as informações e ações compatíveis com sua função;
- os estados confirmados da consulta são `Agendada`, `Confirmada`, `Em andamento`, `Concluída` e `Cancelada`;
- não haverá integração com laboratórios ou sistemas externos de exames;
- assinaturas de prescrições utilizarão ZapSign em sandbox, sem exigência de validade jurídica neste projeto acadêmico;
- operações financeiras utilizarão Asaas em sandbox, com complexidade básica a média;
- anexos de exames utilizarão Cloudinary.

## 7. Arquitetura tecnológica

A decisão arquitetural atual é:

- **Aplicação web full-stack:** Reflex;
- **Linguagem:** Python;
- **Banco de dados:** PostgreSQL;
- **Arquivos de exames:** Cloudinary;
- **Assinatura de prescrições:** ZapSign sandbox;
- **Processamento financeiro:** Asaas sandbox.

Reflex é a tecnologia obrigatória para a aplicação web. Não introduzir React, Next.js, Vue, Angular, Streamlit, Express, FastAPI ou outro framework de aplicação sem uma mudança arquitetural explicitamente aprovada.

O pacote Python da aplicação Reflex é `vitta_one/`. O diretório `openspec/` é reservado aos artefatos do OpenSpec.

## 8. Segurança e integridade

O frontend não deve ser usado como mecanismo de autorização. Regras de acesso, validações e regras de negócio devem ser aplicadas no lado servidor da aplicação.

Credenciais de banco, Cloudinary, ZapSign e Asaas não podem ser hardcoded ou versionadas. Dados clínicos e pessoais devem ser tratados como sensíveis e não devem ser expostos desnecessariamente em logs ou mensagens de erro.

## 9. Estratégia de desenvolvimento

O projeto será desenvolvido incrementalmente com OpenSpec. A visão global do domínio deve permanecer estável, enquanto comportamentos detalhados e decisões técnicas específicas são definidos change por change.

Não implementar todo o banco, todas as telas ou todos os módulos antecipadamente. Cada mudança deve possuir escopo verificável e estratégia de validação.

## 10. Pontos ainda em aberto

Permanecem para refinamento em changes específicas:

- regras exatas de transição entre os estados de consulta;
- quais atores podem executar cada transição em cada momento;
- estrutura detalhada de telas e ações de cada painel por role.

Esses pontos não devem ser preenchidos por suposição.

## 11. Fonte de verdade

- `docs/project-overview.md`: visão global e decisões estáveis;
- `docs/domain-model.md`: conceitos e relacionamentos do domínio;
- `AGENTS.md`: regras operacionais para agentes;
- `openspec/config.yaml`: contexto permanente dos workflows;
- `openspec/specs/`: comportamento consolidado após changes arquivadas;
- `openspec/changes/`: mudanças em planejamento ou implementação.
