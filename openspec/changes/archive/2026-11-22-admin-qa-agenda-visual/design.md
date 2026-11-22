# Desenho técnico — Agenda QA

- **Framework:** Reflex 0.9.10.post2; manter rotas de página e eventos State existentes.
- **Autorização:** `AdminAgendaPreviewState` independente usa `admin_agenda_snapshot`; esta revalida `VITTA_ONE_LOCAL_ADMIN_PREVIEW`, sessão e role. Sem importar handlers mutáveis da Recepção.
- **Consulta:** `list_availability_slots` do serviço existente é reutilizado no período local convertido para UTC. A projeção de consultas consulta apenas ID, médico, horário e estado; não consulta tabelas/colunas clínicas nem paciente.
- **Frontend:** um calendário de apresentação em `vitta_one/ui/calendar_components.py` reutilizado em `/admin/horarios` e `/admin/agenda`; apenas os handlers variam conforme o contexto.
- **Performance:** leitura mensal limitada temporalmente; o cliente recebe células agregadas e detalhes do dia selecionado, com paginação de 20 itens.
- **Estados:** loading limpa resultados antigos, erro genérico com retry, ausência de horários/consultas com mensagem compacta; flag ou role inválida redireciona.
- **Persistência:** nenhuma migration; esta mudança não escreve no banco.
- **Riscos:** leitura mensal da base proporcional à quantidade de slots e consultas dos profissionais. Revisar SQL de agregação se escala de QA aumentar.
