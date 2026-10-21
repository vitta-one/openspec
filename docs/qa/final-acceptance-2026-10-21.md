# Homologação final: formulário, experiência e regras do Vitta-One — 21/10/2026

## Escopo da entrega ao professor

Jornada principal: **Recepção cadastra paciente → envia convite com consentimento → paciente ativa e faz login → escolhe especialidade/médico/horário → confirma → a mesma consulta aparece na agenda da Recepção e do Médico → Recepção confirma chegada → Médico chama e atende**.

Jornada paralela de pronto-atendimento avulso não cria uma Consulta fictícia, mas possui prontuário e prescrição próprios.

## Evidência e critérios

Base: capturas fornecidas pelo solicitante da QA da PR #318, inspeção de formulários/serviços na `develop`, validação Python/PostgreSQL e Chromium isolado com identidades sintéticas. A integração com Resend real não é simulada como confirmação de entrega.

A bateria de navegador executa testes de acesso por perfil, formulário de ativação e autogendamento, máscara e persistência do telefone, CPF, atendimento, prescrição, responsividade de 320/375/768/1280 px, navegação por teclado nos fluxos críticos e capturas de rotas protegidas.

| Passo | Tela ou operação | Situação esperada / verificada | Evidência principal |
| --- | --- | --- | --- |
| 1 | Login por papel | Conta com sessão válida cai apenas no workspace autorizado | Testes `test_auth_*`, navegador login |
| 2 | Recepção → Pacientes | CPF aceito numérico/mascarado, validação por dígitos, telefone com DDD 10/11 números; máscara em digitação/colar | `test_patient_identity_input_masks_and_client_validation`, `test_final_input_validation.py` |
| 3 | Identidade operacional | Dados persistem sem pontuação, CPF não duplica, telefone salvo reaparece formatado | `test_reception_registers_patient_then_opens_its_agenda`, edição + reload |
| 4 | Convite e ativação | Consentimento explícito, código único temporário, e-mail válido, senha com mínimo de 12; não enviar senha ao Reflex State | `test_patient_portal_and_role_agendas.py`, teste HTTP do Chromium e `test_patient_activation_rejects_incomplete_form_before_submitting` |
| 5 | Agenda do paciente | Só especialidade/médico ativos, slots reais e disponíveis; confirmação e conflito transacional | `test_patient_self_scheduling.py`, `test_patient_books_own_appointment_and_both_staff_agendas_update` |
| 6 | Horário forjado | Não aceitar slot fora dos próximos 45 dias nem seleção incompatível com especialidade/profissional | `test_patient_cannot_forge_out_of_window_availability`, RBAC |
| 7 | Agenda da recepção e médico | Mesma Consulta persistida por ID, sem apontar para outro paciente | Testes de integração e Chromium entre papéis |
| 8 | Chegada, fila, médico | Consultas marcadas seguem check-in; passagem avulsa segue sua própria fila | `test_reception_contextual_actions_use_authorized_agenda_flows`, `test_walkin_receipt_to_clinical_prescription_and_review` |
| 9 | Telas administrativas | Administração, especialidades e profissionais; filtros, formulários e estados reais | `test_final_visual_audit_admin_workspace_routes`, demais QA |
| 10 | Responsividade | Telas sem overflow do documento; opções principais do menu totalmente visíveis no mobile | `test_final_visual_audit_reception_workspace_routes`, `test_final_visual_audit_doctor_workspace_routes` |

## Problemas observados e correções

1. CPF e telefone não tinham máscara de digitação. Agora têm formatação progressiva e CPF com checagem de dígitos no browser; o banco continua normalizando para dígitos.
2. Muitos formulários desativavam a validação nativa. Cadastro/busca, convite, profissional e ativação foram ajustados para usar pistas de formulário do navegador antes de ir ao servidor; validação server-side continua obrigatória.
3. O endpoint de ativação recebia POST via `form.submit()`, que ignora constraints nativas. Agora a página chama `reportValidity()` antes de enviar sem serializar a senha no estado do Reflex.
4. CPF e telefone podiam ser normalizados removendo caracteres arbitrários de requisições programáticas. O servidor agora rejeita caracteres fora das gramáticas aceitas.
5. O autogendamento mostrava somente 45 dias, mas a validação de seleção não impunha o limite contra payload forjado. O servidor agora reforça o mesmo horizonte.
6. O seletor de médico exibia um identificador de cadastro interno gerado automaticamente. O portal do paciente passa a mostrar nomes legíveis.
7. Em 320–375 px, a navegação de Recepção/Médico podia cortar abas no scroller horizontal. Menu compacto agora distribui as ações em linhas visíveis.

## Cobertura visual — capturas sintéticas

- Administração: `audit-admin-admin-{1280,375,320}px.png`, `audit-admin-admin-especialidades-*.png`, `audit-admin-admin-profissionais-*.png`.
- Recepção: `audit-recepcao-recepcao-*.png`, `audit-recepcao-recepcao-agenda-*.png`, `audit-recepcao-recepcao-pacientes-*.png`, `audit-recepcao-recepcao-fila-*.png`.
- Médico: `audit-medico-medico-*.png`, `audit-medico-medico-agenda-*.png`, `audit-medico-medico-pacientes-*.png`.
- Paciente: `paciente-autogendamento-{1280,375,320}px.png`, confirmação e agenda integrada.
- Atendimento: `pronto-atendimento-clinico-*.png`, revisão de finalização e diálogos de prescrição.
- Cadastro: `revisao-mascaras-cpf-telefone-375px.png`, `agenda-cpf-validado.png`, ativação inválida.

As capturas são geradas por `qa_browser/prescription_browser.py` em PostgreSQL descartável e publicadas como artifact no workflow `QA Prescrições com Chromium`.

## Limitações e aprovações adicionais

- **Não afirmar conformidade WCAG/LGPD ou 100% de ausência de defeitos** apenas por screenshots e suíte automatizada. É recomendável revisão humana com leitor de tela, teclado e dispositivos físicos.
- **Resend real:** validar envio e recebimento com remetente verificado e caixa autorizada; status `ACCEPTED` do provedor não significa e-mail entregue.
- **Ambiente não descartável:** usar backup, plano de migrações e revisão do deploy; a PR não configura nem publica produção.
- **Dados clínicos:** toda demonstração de QA usa apenas identidades e sintomas sintéticos; uso clínico real exige revisão própria de privacidade, segurança e regras assistenciais.
