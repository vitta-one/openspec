# Auditoria da área de Recepção — 15/10/2026

Escopo revisado antes da primeira evolução P0 do dashboard. As classificações descrevem o código integrado em `develop` no commit `19fbc4f5ec2c2d06a94e0872ebc6832c5f3e13f2`; itens futuros são propostas, não funcionalidades prontas.

| Módulo | Funcionalidade | Situação | Problema identificado | Solução proposta | Prioridade | Arquivos afetados |
|---|---|---|---|---|---|---|
| Dashboard | Indicadores do dia e fila | Existente e funcional | Quatro cards deixam chegadas confirmadas e pendências fora da hierarquia principal | Exibir seis métricas com período e definição explícitos | P0 | `vitta_one/reception/dashboard/components.py`, `state.py`, `service.py`, `application.py`, `vitta_one/ui/pages.py`, `vitta_one/ui/components.py` |
| Dashboard | Próximas consultas | Existente, UX insuficiente | Lista não mostra situação operacional nem ação por item | Mostrar situação `Agendada` e link para a Agenda; manter somente dados operacionais | P0 | `components.py`, `state.py` |
| Dashboard | Pendências de chegada | Parcialmente implementada | Existe contagem, sem lista dos atendimentos que precisam de revisão | Buscar até cinco consultas elegíveis e permitir abrir a Agenda; não inferir falta | P0 | `service.py`, `state.py`, `components.py` |
| Dashboard | Estados assíncronos | Parcialmente implementada | Valores zero aparecem antes da primeira leitura; em falha não há tentativa visível no conteúdo | Distinguir carregamento, leitura concluída e erro com nova tentativa | P0 | `state.py`, `components.py` |
| Dashboard | Consultas ao banco | Existente, com limitação técnica | Contagens são executadas em dez consultas sequenciais | Agrupar métricas de consulta e fila em duas projeções; manter consultas separadas para as duas listas | P0 | `service.py`, `tests/test_reception_dashboard.py` |
| Agenda | Agendamento, reagendamento, cancelamento e check-in | Existente e satisfatória para este escopo | Fluxo de presença já existe; confirmação direta no dashboard poderia registrar uma chegada não observada | Reutilizar a Agenda e seus services; nenhum novo check-in no dashboard | Mantida | `appointment_scheduling/`, `ui/appointment_components.py` |
| Pacientes | Identificação, busca e cadastro básico | Parcial | Diretório completo/paginado e perfil não fazem parte do fluxo atual revisado | Tratar em change futura, sem adicionar campos nesta entrega | P0 futuro | `patient_queue/`, `ui/queue_components.py` |
| Fila | Fila ativa, entrada avulsa, reavaliação e retirada | Existente e funcional | Não há necessidade de alterar transições para apresentar distribuição no dashboard | Manter ownership do módulo e apresentar somente totais existentes | Mantida | `patient_queue/`, `ui/queue_components.py` |
| Atendimento clínico | Leitura e ações clínicas | Existente e protegido | O dashboard não precisa acessar prontuários nem chamar transições clínicas para cumprir seu papel operacional | Manter projeção somente leitura; não expor campos clínicos nem chamar operações de Médico | Fora do escopo | `vitta_one/consultation_care/application.py`, `auth/authorization.py`, `models/` |
| Segurança | Autorização de Recepção | Existente e server-side | A change que formalizou as subrotas continuava ativa após o merge | Consolidar os requisitos e arquivar a change com evidências de PR/CI | P0 | `vitta_one/auth/authorization.py`, `vitta_one/auth/state.py`, `vitta_one/auth/roles.py`, `vitta_one/ui/pages.py`, `openspec/specs/access-control/spec.md`, `UX-CONTRACT.md` |
| Modelos | Pacientes, consultas e fila | Suficientes para este dashboard | Sem definição aprovada para tempo médio de espera ou classificação automática de ausência | Não criar modelo, migration, regra clínica, no-show ou tempo de espera | Fora do escopo | `models/`, sem alterações |
| UI e acessibilidade | Design system e layouts responsivos | Base existente; verificação específica necessária após a alteração | Link dos cards não tinha regra local de foco visível; lista precisa preservar ações em telas estreitas | Reutilizar tokens/primitivos e adicionar foco visível/reflow no dashboard | P0 | `assets/styles.css`, `reception/dashboard/components.py` |

## A. Estado atual

PR #309 entregou o dashboard inicial, quatro rotas de Recepção, leitura server-side, RBAC e fluxo de check-in existente na Agenda. A implementação já tinha testes de dados, fuso e roles; CI registrou 184 testes Pytest, 8 validações OpenSpec, compilação Reflex e 17 testes Chromium.

## B. Problemas encontrados

- UX/UI: chegadas confirmadas e pendências estavam no rodapé; a lista de próximas consultas não incluía estado ou ação por linha.
- Arquitetura/performance: o serviço executava dez round-trips para métricas e prioridades.
- Estado assíncrono: zero inicial não distinguia “ainda carregando” de “sem registros”.
- Modelagem/negócio: métricas de espera e classificação de falta não têm definição aprovada; nenhuma será presumida.
- Segurança: nenhuma falha encontrada nos guards server-side revisados; a consolidação documental da change pós-merge estava pendente.
- Fluxos operacionais: check-in, agenda, pacientes e fila já possuem rotas/serviços; o dashboard deve encaminhar para esses fluxos.
- Acessibilidade: o card-link carecia de foco visível específico, e as listas precisam quebrar linha em viewport estreita.

## C. Design proposto

Seis KPIs factuais, ação primária para agendar e atalho para cadastro, próxima consulta com estado operacional e link para Agenda, fila por prioridades existentes e seção “Precisa da sua atenção” com consultas cujo horário passou hoje sem chegada confirmada. Não mostrar conteúdo clínico, sinal de conexão não verificável, tempo de espera, urgência ou ausência inferida.

## D. Plano técnico

Agrupar contagens no serviço read-only e adicionar uma lista limitada de pendências; propagar dados tipados pelo State; compor o dashboard com as primitivas existentes; atualizar contrato UX e especificações; testar contagens, limite/ordem da lista e número de consultas SQL. Nenhum modelo, migration, autenticação ou regra de transição é alterado.

## E. Plano incremental

1. Consolidar e arquivar `restructure-reception-workspace` após verificar as evidências do PR #309.
2. Implementar somente o refinamento P0 do dashboard nesta change.
3. Validar os testes e workflows do repositório, corrigir falhas e abrir PR para `develop`; não fazer merge.
4. Planejar diretório de pacientes, agenda visual, monitoramento e relatórios em changes futuras, apenas após dependências e regras estarem definidas.
