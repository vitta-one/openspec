# QA visual completo — Vitta-One

## Objetivo

Toda PR para `develop` que alterar a aplicação, os testes de Chromium ou o workflow de QA executa a suíte existente de navegador e, em seguida, captura **as telas pertinentes ao fluxo do pronto-socorro** do Vitta-One em Chromium real.

Os screenshots são feitos a partir de uma aplicação Reflex em execução com PostgreSQL 16 **descartável** e contas `@example.invalid`. Nenhuma tela de produção, conta de pessoa real ou prescrição verdadeira deve ser utilizada.

## Cobertura

| Perfil ou situação | Rotas |
| --- | --- |
| Público | `/login`, `/ativar-paciente` |
| Administrador | `/admin`, `/admin/especialidades`, `/admin/profissionais` |
| Prévias de Admin (apenas QA isolado) | `/admin/recepcao`, `/admin/atendimento`, `/admin/pacientes`, `/admin/financeiro` |
| Recepcionista | `/recepcao`, `/recepcao/pacientes`, `/recepcao/fila` |
| Médico | `/medico`, `/medico/pacientes`, `/medico/prescricao/[prescription_id]` |
| Financeiro | `/financeiro` |
| Estados de autorização | `/primeiro-acesso`, `/acesso-negado` |

**Total:** 18 telas distintas em três viewports: desktop (1440 × 900), tablet (768 × 1024) e celular (375 × 812), resultando em **54 capturas PNG**, desde que todos os fluxos sejam acessíveis.

**Atenção:** a galeria não é aceite do pronto-socorro completo. Os testes legados ainda usam consultas programadas para dados de Prescrição e a migração clínica para `QueueEntry` está documentada na [PR #316](https://github.com/vitta-one/openspec/pull/316). O portal do paciente e as rotas de Agenda não são incluídos na galeria enquanto forem dependentes de agendamento.

A raiz `/` é uma rota de redirecionamento, não uma tela estável; o teste cobre a página de login de entrada em seu lugar. A rota de impressão usa a Prescrição sintética do fixture.

## Como acessar as capturas

1. Abra a PR no GitHub e entre na aba **Checks**.
2. Abra **QA Prescrições com Chromium → chromium-qa**.
3. Vá para a execução do workflow em **Actions**, seção **Artifacts**.
4. Baixe `vitta-one-chromium-all-screens`.
5. Abra `screenshots/manifest.json`: cada registro relaciona perfil, rota, viewport, caminho do PNG e resultado `PASS`, `FAIL` ou `BLOCKED`.
6. Veja os arquivos `screenshots/desktop-*.png`, `screenshots/tablet-*.png` e `screenshots/mobile-*.png` lado a lado.

Os artefatos ficam disponíveis por 90 dias. Se uma captura falhar, o script tenta salvar a tela de erro e registra o motivo no manifesto; **falhas não são reportadas como aprovação**.

## Garantias e limites

- O workflow exige `VITTA_ONE_QA_DISPOSABLE_DATABASE=yes` e PostgreSQL CI local antes de criar identidades fictícias.
- A prévia de Administrador só é habilitada nesse ambiente isolado e permanece protegida no servidor.
- Cada contexto tem sessão própria, login do perfil real e navegação para as rotas permitidas.
- São checados URL, conteúdo esperado, ausência de tela vazia, exceções JavaScript observadas e overflow horizontal.
- As capturas complementam, mas **não substituem**, os testes de ações, teclado, RBAC e prescrições da suíte E2E existente.
- Novas rotas implementadas deverão ser adicionadas em `qa_browser/capture_all_screens.py`; não considerar a matriz automática completa após criar páginas sem atualizar esse inventário.
- A inspeção visual humana dos PNGs ainda é necessária para avaliar hierarquia, padding, tipografia e experiência de uso.

## Comando no CI

```bash
python -m scripts.qa_seed_prescriptions
python -m scripts.qa_seed_visual_accounts
# iniciar Reflex conforme o workflow
python -m pytest qa_browser/prescription_browser.py -q
python -m qa_browser.capture_all_screens
```

Não execute os seeds em banco persistente. A execução oficial é `.github/workflows/qa-prescriptions-browser.yml`.
