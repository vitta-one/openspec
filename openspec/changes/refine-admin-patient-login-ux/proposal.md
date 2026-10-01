## Why

O refinamento visual premium já consolidado melhorou a identidade do Vitta-One, mas três fluxos ainda apresentam atrito operacional observado na validação visual local:

- a Administração mantém formulários extensos de especialidade e profissional permanentemente abertos, competindo com o diretório que deveria ser a informação principal;
- a visualização local de Pacientes usa uma coluna lateral e um grande estado vazio, o que dificulta localizar, percorrer e agir sobre pacientes persistidos;
- o login perde eficiência em viewports intermediários ou baixos, e o controle de revelar senha precisa permanecer geometricamente centralizado dentro do campo.

A mudança deve melhorar a UX sem ampliar permissões, sem criar funcionalidades de negócio inexistentes e sem introduzir dados fictícios.

## What Changes

- Mover criação e edição de especialidades para um diálogo modal controlado, aberto a partir de ações explícitas da Administração.
- Mover criação e edição de profissionais para um diálogo modal controlado, reutilizando o formulário e as validações existentes.
- Manter listas de especialidades e profissionais como conteúdo principal do diretório administrativo.
- Preservar estados de loading, erro e sucesso e fechar o diálogo somente após operação bem-sucedida ou cancelamento explícito.
- Reestruturar o preview local de Pacientes para usar uma busca única no topo, lista paginada de pacientes persistidos e seleção por checkbox.
- Permitir no máximo um paciente selecionado por vez no preview local, exibindo uma barra contextual com ações somente leitura compatíveis com o modo QA.
- Exibir detalhes e histórico operacional somente para o paciente selecionado, sem conceder mutações de Recepção ao Administrador.
- Manter paginação e busca sobre dados reais já carregados pelo preview local, resetando a página quando a consulta muda.
- Centralizar o controle de revelar/ocultar senha dentro do campo e preservar nome acessível e estado pressionado.
- Melhorar o responsivo do login para desktops baixos, tablets e mobile, priorizando formulário, legibilidade e alcance das ações sem clipping.
- Atualizar o contrato de UX para registrar diálogos administrativos, paginação/seleção de pacientes e comportamento responsivo do login.

## Capabilities

### Modified Capabilities

- `access-control`: comportamento responsivo e acessível da tela de login e do controle de revelar senha.
- `professional-specialty-management`: criação/edição por diálogo modal e diretório como superfície principal.
- `patient-reception-queue`: visualização local do Administrador para pacientes persistidos com busca, paginação e seleção contextual somente leitura.

### New Capabilities

Nenhuma.

## Out of Scope

- alterar regras de autorização ou transformar o Administrador em Recepcionista/Médico;
- cadastro, reavaliação, retirada, chamada ou finalização de fila pela tela de Pacientes do Admin;
- paginação remota/server-side da Recepção nesta change;
- prontuário, diagnóstico, prescrição, exames ou financeiro;
- agenda e agendamento além da change `add-appointment-scheduling`;
- novos modelos ou migrations;
- novos dados de demonstração.

## Impact

- altera componentes Reflex de Administração, Pacientes e Login;
- adiciona estado de abertura/fechamento de diálogos ao `AdminDirectoryState`;
- adiciona estado e computed vars de paginação/seleção ao `AdminPreviewState`;
- atualiza `assets/styles.css` e `UX-CONTRACT.md`;
- preserva serviços, modelos, banco e autorização existentes;
- exige `pytest`, `reflex compile --dry` e validação OpenSpec antes de merge.
