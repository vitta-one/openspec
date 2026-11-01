## ADDED Requirements

### Requirement: Navegação administrativa distingue operações e inspeção local
O sistema MUST apresentar na central administrativa apenas links para rotas administrativas reais e autorizadas. A sidebar MUST distinguir destinos operacionais de visualizações locais de inspeção QA, que MUST permanecer indisponíveis quando o modo QA autorizado estiver desabilitado. Toda rota e operação MUST continuar exigindo autorização no servidor.

#### Scenario: Administrador navega nas tarefas da clínica
- **WHEN** um Administrador abre `/admin` e escolhe criar funcionário, consultar profissionais, especialidades, horários ou configurações
- **THEN** a navegação aponta para a rota implementada correspondente e mantém a indicação de página ativa

#### Scenario: Inspeção QA não habilitada
- **WHEN** um Administrador abre a sidebar sem o modo QA explicitamente autorizado
- **THEN** a navegação não oferece as rotas de inspeção local como tarefas operacionais

#### Scenario: Acesso direto indevido a visualização QA
- **WHEN** uma sessão sem permissão ou com modo QA desabilitado solicita diretamente uma rota de inspeção
- **THEN** o servidor nega a operação sem retornar dados clínicos protegidos

### Requirement: Navegação administrativa é utilizável em telas estreitas
O sistema MUST manter os destinos administrativos alcançáveis por teclado e sem overflow horizontal em viewport móvel. O controle de menu MUST informar o estado expandido e MUST permitir fechamento acessível.

#### Scenario: Administrador usa menu móvel
- **WHEN** o Administrador abre o menu em viewport estreita
- **THEN** o menu apresenta os destinos permitidos e um controle de fechamento alcançável pelo teclado, preservando foco visível
