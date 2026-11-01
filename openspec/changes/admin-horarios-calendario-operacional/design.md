# Design — Agenda médica administrativa operacional

## Baseline

A PR #325 já adicionou o calendário mensal a `vitta_one/ui/appointment_components.py`. A change reutiliza essa implementação, com `AdminAvailabilityState` em `vitta_one/appointment_scheduling/state.py` e as operações autorizadas de `application.py`.

## Fluxos

1. **Selecionar médico:** um select acima das abas. Seu valor é persistido no State; ao alterar, o servidor revalida a sessão administrativa e busca agenda e expediente daquele médico. A mudança não mistura dados entre profissionais.
2. **Consultar disponibilidade:** aba inicial. O calendário consulta slots persistidos do mês e aceita selecionar dia vazio. Apenas dias de meses adjacentes não são selecionáveis. A seção do dia oferece contagens e linhas compactas, ordenadas pela consulta existente.
3. **Editar expediente:** formulário existente continua registrando um intervalo contínuo, com texto explícito. O resumo do expediente salvo é independente dos valores ainda não submetidos no formulário.
4. **Criar avulso:** formulário usa data e hora separadas; o serviço valida futuro, duplicidade e profissional ativo. Após persistir, exibe mês e data correspondentes na aba calendário.
5. **Desativar:** botão abre diálogo acessível de confirmação para slot disponível. A mutação revalida role, status e integridade no servidor; horários reservados nunca recebem a ação.

## Segurança e integridade

- Nenhum identificador da UI é uma autorização; `application.py` exige Administrador.
- `set_availability_slot_active` usa lock e rejeita `BOOKED`.
- `save_weekly_schedule` e `create_availability_slot` reutilizam constraints e transações existentes.
- Quantidades são derivadas somente dos slots consultados.
- O select omite identificadores internos `INT-...`; homônimos possuem desambiguação.
- Sem migrations e sem alterações no domínio persistido.

## UX e acessibilidade

Preservar tokens e primitives Reflex/Radix de `DESIGN.md`, `UX-CONTRACT.md` e `assets/styles.css`. Calendário com `aria-label`, `aria-pressed` e foco visível; diálogos Radix; texto explícito para estados; campos nativos com `lang=pt-BR`; feedback de erros inline; linhas fluidas no mobile.

## Homologação pendente

Confirmar `reflex compile --dry`, testes Pytest e QA Playwright/Chromium com dados sintéticos e viewport 320/390/768/1024/1440. O locale nativo de date/time depende também da configuração do navegador e precisa de validação visual.
