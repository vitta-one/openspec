# Design — Modais e operações de especialidades

- **UI:** manter `rx.dialog` (Radix), o campo/label compartilhados e `vitta-dialog-content`. A função de formulário será parametrizada pelo modo criar/editar. Erros aparecem após o input, associados via `aria-describedby`, sem duplicação no painel.
- **State:** `specialty_form_error` será local ao modal. `is_submitting` bloqueia reentrância tanto no evento quanto no botão. Cancelar/Escape apagam formulário; erros preservam os valores.
- **Leitura autorizada:** `begin_specialty_edit` consulta o registro persistido via `admin_get_specialty`, com RBAC de Administrador, antes de abrir.
- **Concorrência:** `rename_specialty` e `set_specialty_active` usam row lock e aceitam estado/nome esperado, evitando ações sobre estado desatualizado. Chamadas legadas sem valor esperado continuam aceitas.
- **Persistência:** operações continuam no modelo `Specialty` e nas transações existentes; `ProfessionalSpecialty` permanece intocado. Conflitos e validações são rejeitados no servidor.
- **Feedback:** toast após persistência; erro recuperável do modal permanece inline; status e filtros são atualizados a partir da consulta persistida. O CSS global já mantém o toaster acima dos overlays.
- **Responsividade/a11y:** preservar Radix para foco inicial, armadilha Tab, Escape e restauração de foco. Usar botões nativos e variantes existentes; validar navegador em 320/390/768/1024/1440px.

## Riscos
- Testes SQLite verificam regras; `FOR UPDATE` deve ser homologado com concorrência real no PostgreSQL QA.
- Foco e leitores de tela exigem teste real no Chromium, não apenas compilação.
