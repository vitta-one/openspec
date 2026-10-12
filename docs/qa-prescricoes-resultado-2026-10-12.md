# Aceite da SDD — Prescrições clínicas

**Data:** 12/10/2026 · **Capability:** `clinical-prescription` · **Repositório:** `vitta-one/openspec`.

## Escopo validado

A implementação de Prescrições permanece sem assinatura digital, sem prontuário oficial assinado e sem integração externa. A mudança foi conciliada com **235/235 tarefas** e **22 requisitos/46 cenários normativos**. O objetivo deste documento é comprovar apenas o escopo acadêmico implementado — **não certificar um sistema para atendimento clínico em produção**.

## Execuções e resultados

| Evidência | Ambiente e escopo | Resultado |
| --- | --- | --- |
| [Chromium #38273941455](https://github.com/vitta-one/openspec/actions/runs/38273941455) | Reflex full-stack em modo produção, Chromium headless/Playwright, PostgreSQL 16 isolado, duas identidades MEDICO e consultas/prescrições fictícias | **6 testes E2E aprovados** |
| [CI Python #38273939961](https://github.com/vitta-one/openspec/actions/runs/38273939961) | Migrações desde base vazia PostgreSQL 16, OpenSpec CLI estrito e pytest | **7/7 OpenSpec, 151 testes Python, migrations/compile aprovados** |
| [Chromium #38273514533](https://github.com/vitta-one/openspec/actions/runs/38273514533) | Após correção do layout móvel de badges no histórico | **6/6 E2E aprovados** |
| [Revisão das capturas #38274780820](https://github.com/vitta-one/openspec/actions/runs/38274780820) | PNGs com dados sintéticos: tela de impressão, diálogos e histórico em 320/375/768 px | Conferida visualmente pelo assistente; sem corte horizontal aparente |

## Rastreabilidade das sete tarefas finais

| Tarefa | Critério e evidência |
| --- | --- |
| **10.18** | `qa_browser/prescription_browser.py`: botão acionado via Enter, Tab/Shift+Tab nos campos, labels e foco testados em Chromium; estilo `:focus-visible` no CSS. |
| **10.20** | Emulação `prefers-reduced-motion: reduce` e verificação da duração de animação e token `--vitta-focus`; capturas preservam cores/estrutura. |
| **11.8** | Testes de foco inicial de Nova, Adicionar, Editar, Observações, Remover e Excluir; Esc fecha, e nova Prescrição restaura foco no trigger após correção. |
| **13.8** | Consultas atuais e histórico clínico concluído com prescrição real de teste: 320, 375 e 768 pixels sem scroll horizontal; correção pontual do grupo de badges do histórico. |
| **15.9** | Login como Médico B; URL direta de impressão pertencente ao Médico A resulta em acesso negado, inclusive após reload, sem texto clínico. |
| **15.10** | Contexto novo, sem cookie/sessão; URL direta redireciona ao login sem conteúdo clínico. |
| **19.12** | Falhas E2E diagnosticadas e corrigidas: restauração de foco e overflow mobile; CI Python e Chromium aprovados novamente. |

## Mudanças corretivas

1. `vitta_one/ui/queue_components.py`: restaurar o foco no botão Nova prescrição ao fechar o diálogo.
2. `vitta_one/ui/queue_components.py`: na largura mobile, cabeçalho de histórico passa a empilhar conteúdo e permitir quebra das badges; sem esconder overflow artificialmente.
3. `.github/workflows/qa-prescriptions-browser.yml` + `qa_browser/prescription_browser.py` + `scripts/qa_seed_prescriptions.py`: suíte separada da descoberta pytest usual, fixture obrigatoriamente descartável com duas contas médicas e históricos sintéticos.

## Limites explícitos deste aceite

- A revisão visual foi feita **sobre capturas reais geradas pelo Chromium**, e não mediante execução presencial em Android, iPhone ou leitor de tela assistivo.
- Nenhuma pessoa da equipe fez homologação manual formal durante esta revisão. A seção de assinatura humana de `docs/qa-prescricoes-aceite-2026-10-12.md` permanece disponível; **não foi preenchida artificialmente**.
- O app **não tem assinatura digital clínica**. Não utilizar a impressão como documento eletrônico assinado.
- Screenshots são inteiramente sintéticos. O [artefato visual do Chromium #38274780820](https://github.com/vitta-one/openspec/actions/runs/38274780820/artifacts/11758033042) tem retenção registrada até **10/01/2027**. Logs de CI e arquivos de teste são versionados.

**Decisão documental:** os critérios verificáveis das 235 tarefas acadêmicas receberam evidência, inclusive o browser QA dos últimos sete itens. Consolidar `clinical-prescription` em `openspec/specs/` e preservar a change original em `openspec/changes/archive/`. Homologação humana e em dispositivos físicos é recomendada antes de um eventual uso não acadêmico.
