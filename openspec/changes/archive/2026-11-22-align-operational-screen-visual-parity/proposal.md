## Why

As 16 rotas funcionais já existem, mas a apresentação ainda diverge das referências: a navegação começa expandida em todos os perfis, o painel administrativo não mostra seus indicadores e a Recepção não expõe os estados reais dos e-mails. Esta change aproxima o shell e os painéis das composições de referência sem transformar os exemplos das imagens em dados nem duplicar regras de domínio já implementadas.

## What Changes

- Alinhar shell, navegação, cabeçalhos, superfícies e estados responsivos das 16 rotas aos tokens e às variantes de perfil mostradas nas referências.
- Exibir no início da Administração contagens persistidas de profissionais ativos, especialidades ativas, consultas do dia local e contas de equipe, com destinos de tarefa existentes.
- Exibir na Recepção indicadores agregados, limitados aos últimos 30 dias, de mensagens aceitas pelo Resend, entregues, falhas e ainda pendentes/indeterminadas.
- Preservar dados, formulários, filtros, paginação, eventos, RBAC e estados vazios existentes; nenhuma ação visual poderá substituir a operação de domínio correspondente.
- Registrar comparação visual das 16 rotas em 1768×890 e evidências responsivas nas larguras de 320, 390, 768, 1024 e 1440 pixels com dados sintéticos, sem versionar as imagens locais de referência.

## Capabilities

### New Capabilities
- `operational-screen-presentation`: contrato compartilhado de apresentação e navegação responsiva para as 16 rotas operacionais e suas variantes de perfil.
- `administration-dashboard`: indicadores administrativos agregados e navegação para tarefas existentes.

### Modified Capabilities
- `reception-operational-dashboard`: acrescenta métricas agregadas e autorizadas dos estados de notificações de agenda.

## Impact

- Afeta componentes Reflex compartilhados, dashboards de Administração e Recepção, estilos em `assets/styles.css` e testes de projeções/estados.
- Acrescenta consultas de leitura aos modelos existentes de autenticação, profissionais, especialidades, consultas e notificações; não altera schema, migrations, integrações HTTP ou contratos de provedor.
- Não adiciona dependências. As integrações Asaas e Resend existentes permanecem Sandbox/configuráveis; credenciais e endpoint público continuam necessários para homologação real.
