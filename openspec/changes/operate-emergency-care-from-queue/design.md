# Design técnico — pronto-socorro por fila

## Fonte da verdade
`QueueEntry` é o episódio operacional: `patient_id`, `entered_at`, `priority`, `status`, `doctor_user_id`, `called_at` e `finished_at`. A fila existente ordena prioridade VERMELHO → AMARELO → VERDE e chegada crescente dentro da prioridade. Não inferir gravidade clínica nem horário futuro.

## Jornadas
1. **Recepção:** localizar/cadastrar paciente; informar relato e prioridade; cadastrar passagem (`AGUARDANDO`); reavaliar ou retirar enquanto autorizado.
2. **Médico:** reivindicar atomicamente a primeira entrada elegível (`EM_ATENDIMENTO`); carregar o contexto só do paciente reivindicado; salvar prontuário e criar/editar prescrição; finalizar (`FINALIZADO`). Um Médico não mantém dois atendimentos simultâneos.
3. **Paciente:** acesso ao próprio histórico concluído quando a projeção read-only por `patient.user_id` estiver implementada; não exibir calendário nem dados de terceiros.
4. **Administrador:** profissionais/especialidades/configurações; previews de QA seguem sem mutações clínicas.

## Migração clínica aditiva necessária
- Permitir `ClinicalCareRecord.consultation_id` opcional para legado e adicionar `queue_entry_id` único, referenciando `QueueEntry`. Exigir **exatamente um vínculo** por constraint; não sobrescrever histórico legado.
- Fazer `Prescription.consultation_id` opcional para novos episódios de fila; o vínculo obrigatório continua `clinical_care_record_id`, evitando duplicar o identificador do episódio na prescrição.
- `claim_next_patient`: criar o registro clínico ligado à entrada avulsa no mesmo contexto transacional da chamada; revalidar `doctor_user_id` e locking. Corridas não podem gerar registros duplicados.
- `get_active_record`, `save_active_record`, `list_completed_history_for_patient` e operações de prescrições precisam aceitar episódio de fila sem `Consultation` programada.
- Impressão: paciente, médico/registro, **data real do atendimento** e itens, nunca horário agendado falso.
- Finalização: somente Médico responsável, após revalidar entrada ativa e se os textos pendentes foram salvos; histórico e documento permanecem somente leitura após conclusão.
- Projeção paciente: `Patient.user_id` correspondente à sessão; nenhum histórico clínico de terceiros.

## Garantias
- Migrações somente em PostgreSQL descartável até revisão manual, rollback e verificação de destino; sem exclusão de tabela.
- Consistência server-side sob concorrência; índices `queue_entry_id` e `patient_id`; ausência de dados sensíveis em logs.
- `/recepcao/agenda`, `/medico/agenda` e `/admin/agenda` deixam de ser rotas publicadas; registros legados ficam preservados para futura política de retenção.
- Prévias e testes antigos que ainda usam Consulta agendada devem ser atualizados antes de qualquer merge.

## Interface
Manter fonte, tokens, sidebar e feedback já existentes. A recepção abre a fila real como página inicial, oferece acessos diretos a cadastro e reavaliação, apresenta loading/vazio/erro. O médico trabalha somente na passagem chamada; usuário nunca informa horário agendado. Mobile em coluna única, focos visíveis, modais acessíveis, sem scroll horizontal do documento.
