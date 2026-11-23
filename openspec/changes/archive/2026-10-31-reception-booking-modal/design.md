## Contexto

O Vitta One é monólito modular Reflex 0.9.10.post2. O estado `ReceptionAgendaState` coordena eventos de UI; `reception_schedule_consultation` realiza autorização por role e reserva transacional com locking/constraints existentes. Paciente e slot são persistidos.

## Decisão

- Manter um único diálogo composto em `vitta_one/ui/appointment_components.py`, instanciado pela Agenda e pelo dashboard.
- Usar o mesmo `ReceptionAgendaState` para seleção e confirmação; buscar identidades mínimas com `reception_search_patients` e validar a seleção com `reception_get_patient_identity`.
- Usar `reception_get_agenda` para consultar slots de um profissional em 45 dias, sem inferir intervalos ou inventar datas.
- Usar o calendário mensal no fuso da clínica, reaproveitando os tokens e padrões Vitta One, e exibir apenas slots de estado disponível e horários futuros.
- Confirmar usando `reception_schedule_consultation` e o controle de concorrência existente. Após conflito, atualizar slots e manter paciente/médico.
- Separar falha na persistência de falha na atualização da UI, para impedir incentivo a reenvio após reserva gravada.
- Ao abrir a rota legada, aplicar verificação de acesso específica para o próprio path, mantendo o conteúdo canônico.

## UX, integridade e segurança

O modal usa Radix Dialog com foco contido, suporte a Escape e restauração do foco. Um Alert Dialog confirma descarte de seleção. As etapas têm mensagens inline e botões desabilitados durante carregamento/envio; rótulos e estados não dependem só de cor. Campos clínicos não são incluídos. Nenhum dado real de paciente é colocado em URL ou exibido sem autorização.

## Testes e rollout

Testar calendário e máscara em unitários, autorização para carregar profissionais e especialidade opcional, serviço existente de conflito de slot, navegação pelo dashboard/agenda/ficha, fluxo de confirmação em PostgreSQL QA e Chromium em diferentes resoluções. CI e validação manual são pré-requisitos de merge.
