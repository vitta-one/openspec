# Design — Ficha individual QA de paciente

## Navegação
`/admin/pacientes` apresenta tabela semântica de nome, CPF mascarado e "Ver detalhes". A ficha usa rota Reflex dinâmica e breadcrumb para retorno; busca/página ficam no State durante a navegação, mas são limpas ao trocar de sessão.

## Estado e dados
- `load_patient_list`: revalida sessão/role/flag QA e busca exclusivamente `Patient`; não serializa fila nem prontuário.
- `load_patient_detail`: valida `patient_id` da rota e consulta `Patient` + `QueueEntry` filtrados pelo ID, com autorização prévia.
- `show_clinical_history`: revalida a autorização e a existência do recurso e delega à projeção clínica existente; não busca dados clínicos no carregamento inicial.
- Ao mudar para histórico operacional, descartar a projeção clínica do State.
- Sintomas, prioridades e estados permanecem de leitura restrita no preview QA; CPF completo nunca é enviado à UI.
- Um paciente excluído/inexistente não pode reaproveitar dados de uma ficha anterior.
- A conversão de data/hora utiliza `format_clinic_datetime`, respeitando o fuso configurado.

## Interface
- Tabela compacta de três colunas, CPF na identificação em tela estreita.
- Botões semânticos para alternar entre seções operacionais/clínicas; botão de acesso clínico dispara leitura protegida.
- Indicadores e mensagens distintas de carregamento, vazio, não encontrado e erro.
- Nenhuma ação de escrita de fila ou prontuário.

## Segurança e regressões
A flag QA é verificada no servidor; não basta presença da rota. Não aumentar o acesso do Administrador em produção. Preservar os previews de Recepção, Agenda, Atendimento e Financeiro, que usam seu carregamento atual.
