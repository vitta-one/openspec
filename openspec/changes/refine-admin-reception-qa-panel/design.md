# Design — Painel de acompanhamento administrativo da Recepção

## Arquitetura e permissão
A rota `/admin/recepcao` usa `AdminReceptionPreviewState` exclusivamente para leituras. O serviço `load_reception_preview` começa por `require_local_admin_preview`, que verifica flag QA, sessão e role no servidor a cada carga, atualização manual ou automática. A UI não importa estados de mutação da Recepção.

O novo State é removido do browser na limpeza de sessão de `AuthState`. Os outros previews continuam usando `AdminPreviewState`, sem ampliação do escopo de dados.

## Projeção
- A fila `AGUARDANDO` usa `patient_queue.service.list_waiting_queue`, preservando prioridade → chegada → identificador. Em atendimento é separado na mesma seção ativa.
- Finalizados e retirados permanecem no histórico com filtro por `finished_at` e `withdrawn_at`, não por entrada na fila.
- Métricas atuais independem de período; histórico e agenda usam limites de datas inclusivas no fuso da clínica e UTC exclusivamente no banco.
- O filtro de prioridade afeta dados e indicadores da fila. Situação filtra apenas as listas, sem alterar a semântica dos indicadores.
- A agenda utiliza `Consultation` e `Professional` persistidos, sem duplicar reserva, transições ou autorização de mutações.
- A leitura nunca serializa CPF, sintomas, anamnese, diagnóstico, conduta ou prescrição. A agenda administrativa mostra apenas médico, horário e situação.
- O intervalo de busca é limitado a 31 dias; até 50 linhas por lista são exibidas, com o total real informado.

## Interface
Usar `DESIGN.md`, `UX-CONTRACT.md`, componentes `section_panel`, `empty_state`, `error_banner`, `field_label` e badges existentes. Quatro números compactos, sem marcas coloridas decorativas; seções fila atual, histórico e agenda com alturas naturais. Inputs de data e select Radix têm labels e foco. Mobile empilha seções; duas colunas apenas quando houver largura suficiente.

## Erros e atualização
Loader limpa dados anteriores antes da leitura, sem mostrar lista vazia em caso de falha. Falha operacional não expõe exceções do banco; data/filtro inválidos retornam validação legível. Refresh manual e `rx.moment` a cada 60 segundos passam pelo mesmo serviço seguro. Não há polling fora da rota.

## Riscos e verificações
O Reflex compile e QA Chromium devem verificar os cinco breakpoints, foco e disparo das mudanças de filtro. Consultas são paginadas apenas no limite de projeção (50), com contagem real e sem ação de paginação; avaliar SQL eficiente caso o volume de QA cresça. Não há migration, configuração de infraestrutura, integração externa nem deploy.
