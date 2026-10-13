# QA de aceite — Prescrições clínicas (Vitta-One)

**Data:** 12/10/2026 · **Change:** `add-clinical-prescription` · **Ambiente-alvo:** Vitta-One Reflex + PostgreSQL 16 descartável.

## Estados de evidência

- **CI aprovado:** teste executado automaticamente em GitHub Actions e aprovado, com link da execução e requisito específico.
- **Auditoria de código:** evidência estática versionada, **não** substitui teste de browser.
- **QA humano pendente:** cenário detalhado abaixo, ainda **NÃO EXECUTADO** por operador no navegador.
- **Bloqueado:** comportamento com defeito ou sem ambiente reproduzível; não marcar tarefa como concluída.

> **Atenção:** este documento é um **roteiro executável de QA**, não um certificado de que as interações no navegador foram realizadas. Nenhuma assinatura/aceite humano foi presumido. Nunca registrar dados clínicos reais, CPF completo, tokens ou senhas em screenshots e logs.

## Preparação do ambiente

1. Em ambiente local isolado, iniciar PostgreSQL 16 e aplicar todas as migrations com `reflex db migrate`.
2. Subir o Vitta-One Reflex e autenticar contas de teste separadas de Administrador, Recepcionista, Médico A, Médico B e Financeiro.
3. Criar um paciente **fictício**, um profissional vinculado a Médico A, slot de Agenda, Consulta, confirmação de chegada, chamada pelo Médico A e `ClinicalCareRecord` ativo.
4. Criar uma prescrição com medicamento e orientação **fictícios**, acrescentar dois itens e observações. Manter uma Consulta ainda `EM_ANDAMENTO` e outra `CONCLUIDA`.
5. Para cada passo, registrar plataforma, navegador, viewport, resultado observado e captura com informações clínicas e pessoais mascaradas.

## Matriz de QA de navegador — pendências visuais e de rota

| Tarefa | Passos de execução | Aceite verificável | Estado |
| --- | --- | --- | --- |
| **10.18** — Teclado, labels, foco | No painel Médico, pressionar Tab/Shift+Tab até Nova prescrição; abrir, navegar por todos os campos e botões, submeter inválido e corrigir; ativar via Enter/Espaço. | Todos os campos possuem nome associado; ordem de Tab é previsível; foco visível; ações usáveis sem mouse. | **Chromium aprovado; revisão presencial não executada** |
| **10.20** — Reduced motion/tokens | Repetir fluxo com `prefers-reduced-motion: reduce`; inspecionar foco, bordas, contraste e transições no tema do Vitta-One. | Sem movimentos desnecessários; cores e espaçamentos preservam tokens; contraste legível. | **Chromium aprovado; revisão presencial não executada** |
| **11.8** — Foco inicial | Abrir cada diálogo: nova, adicionar/editar item, editar observações, confirmar exclusão e remoção; usar Esc e reabrir. | Primeiro foco em campo ou ação segura adequada; foco preso no diálogo, restaurado ao fechar; exclusão não é ação inicial. | **Chromium aprovado; revisão presencial não executada** |
| **13.8** — Mobile | Usar viewports 320×640, 375×667 e 768×1024, incluindo histórico aberto e itens extensos. | Sem rolagem horizontal de página; itens e botões acessíveis, sem clipping. | **Chromium aprovado; revisão presencial não executada** |
| **15.9** — URL outro Médico | Copiar a URL `/medico/prescricao/<id>` criada pelo Médico A; acessar em sessão Médico B por endereço direto/reload. | Dados clínicos ausentes; acesso negado pelo servidor; nenhum conteúdo anterior persiste. | **Chromium aprovado** |
| **15.10** — URL sem sessão | Limpar sessão/cookie; abrir diretamente a URL da prescrição, inclusive após reload. | Redirecionar ao login sem renderizar informações clínicas; sem flash de dados antigos. | **Chromium aprovado** |
| **15.11** — Logout | Abrir diálogo preenchido + rota de impressão; fazer logout; navegar para voltar/reabrir. | State do Médico, conteúdo dos diálogos, histórico e documento de impressão limpos; nenhuma exposição por histórico/browser. | **QA E2E pendente** |
| **15.12** — CPF em rota/State | Usar DevTools apenas com dados fictícios; conferir URL, histórico de navegação, parâmetros e payload de print/state. | CPF ausente de URL e estado de impressão; dados pessoais mínimos. | **QA de inspeção pendente** |
| **17.11** — Documento | Abrir impressão com duas prescrições e múltiplos itens, observar PDF preview no navegador. | Paciente, profissional, registro, data da Consulta, todos os itens/posologias/observações, na ordem; sem shell operacional impresso. | **QA visual pendente** |
| **17.12** — Sem assinatura | Conferir documento e prévia de impressão. | Texto literal “Documento sem assinatura digital nesta etapa.” visível; sem selo, QR ou falsa assinatura. | **QA visual pendente** |

## Testes automatizados adicionais neste trabalho

| Tarefa | Teste novo | Gate |
| --- | --- | --- |
| **15.3** | `test_database_failure_never_echoes_sensitive_payload_to_functional_error` | Exceção SQLAlchemy com payload sensível resulta em rollback e erro funcional sem vazamento |
| **17.6** | `test_history_loads_prescriptions_only_for_records_on_selected_page` | IDs do batch de prescrições correspondem exatamente aos registros da página |
| **17.7** | `test_printable_prescription_is_available_to_author_while_consultation_is_active` | Médico autor obtém campos e itens em Consulta `EM_ANDAMENTO` |
| **18.7** | `test_postgresql_prescription_foreign_keys_and_indexes_match_migration` | Catálogo PostgreSQL 16 declara FKs, `ondelete` e índices esperados |

**Resultado CI confirmado:** [run #38267759415](https://github.com/vitta-one/openspec/actions/runs/38267759415) — OpenSpec strict 7/7, PostgreSQL 16/migração aprovada, **145 testes aprovados**, Reflex compile aprovado. Os quatro testes novos passaram; **15.3, 17.6, 17.7 e 18.7** foram conciliados. O CI não executa QA humano nem E2E de navegador. Nenhum checkbox de Prescrições deve ser marcado com base exclusivamente nesta tabela.

## Auditoria de warnings (19.11)

Logs da baseline `develop`: [run #38264642517](https://github.com/vitta-one/openspec/actions/runs/38264642517).

| Aviso observado | Classificação | Tratamento |
| --- | --- | --- |
| Reflex `rx.Model` deprecated desde 0.9.2 | Compatibilidade futura | Registrar dívida técnica; migration/model refactor separado, sem misturar na SDD |
| `rx.App(theme=...)` deprecated desde 0.9.0 | Compatibilidade futura | Atualização controlada após validar versão Reflex |
| Versão Reflex 0.9.10.post2 antiga, sugere 0.10.0 | Atualização futura | Manter pin por enquanto; estudo de migração independente |
| Node `punycode` e `url.parse()` deprecated | Dependências transitivas do build | Avaliar atualização de toolchain no PR específico |
| GitHub Actions `checkout@v4` e `setup-python@v5` usam Node 20 depreciado | Toolchain CI | Planejar atualização das actions e rodar regressão completa |

**19.11 conciliada por auditoria comparativa:** a baseline [#38264642517](https://github.com/vitta-one/openspec/actions/runs/38264642517) e o run [#38267759415](https://github.com/vitta-one/openspec/actions/runs/38267759415) apresentam os mesmos avisos de depreciação identificados acima. Não foi identificado novo tipo de warning nesses logs. Tratar avisos antigos como dívida técnica, sem atualizar framework neste PR. **19.12 permanece pendente** até a execução do QA visual e revisão de regressões.

## Registro de execução humana

Preencher **somente depois do teste real**:

- Commit testado:
- URL do ambiente local e data:
- Browser / SO:
- Responsável:
- Tarefas executadas e resultado (aprovado/reprovado):
- Defeitos e links dos issues/PRs corretivos:
- Capturas anonimizadas (links, sem dados reais):
- Aprovação da revisão / data:

**Critério para arquivar:** OpenSpec strict aprovado, migration + suite + compile aprovados, cobertura específica das pendências validada e resultado real de QA visual/segurança registrado. A existência deste arquivo não autoriza archive.

## Complemento automatizado de State e árvore Reflex

[GitHub Actions #38268988581](https://github.com/vitta-one/openspec/actions/runs/38268988581): **150 passed**, migrations PostgreSQL 16, OpenSpec 7/7, compilação aprovada. O novo `tests/test_clinical_prescription_route_state.py` testa o handler do print com parâmetros de rota e exceções de autenticação/autorização; confirma limpeza no logout e verifica os textos reais da árvore Reflex (com normalização da serialização Unicode). Esses testes sustentam **15.11, 17.11 e 17.12** no nível automatizado. **As verificações visuais e de acesso HTTP no navegador continuam não executadas.** Não registrar checkbox humano como aprovado.

## Complemento de privacidade do print

O [CI #38269431075](https://github.com/vitta-one/openspec/actions/runs/38269431075) aprovou **151 testes**, incluindo `test_print_route_state_does_not_copy_cpf_or_put_it_in_url`. O caso injeta um CPF fictício na projeção de origem e assegura que o carregamento do documento usa somente `prescription_id` numérico, sem copiar o CPF para o estado de impressão. **15.12 reconciliado via teste de State**; DevTools/URL no navegador real segue como recomendação de QA manual para defesa em apresentação.

## Resultado após QA real em Chromium (12/10/2026)

[Workflow E2E #38273941455](https://github.com/vitta-one/openspec/actions/runs/38273941455): **6/6 testes aprovados** com Reflex real e PostgreSQL 16 descartável. Evidências capturadas em 320, 375 e 768 pixels, histórico não vazio, documento HTML e cinco diálogos. Os testes verificaram redirecionamentos efetivos de sessões ausentes e Médico alheio sem renderização de dados fictícios. Foi corrigido o retorno de foco após Esc e o overflow horizontal das badges do histórico. Capturas sintéticas revisadas pelo assistente; **nenhuma homologação por um usuário humano em dispositivo físico foi realizada**. Este último tipo de validação pode ser documentado posteriormente sem falsificar a trilha atual. Detalhes em `docs/qa-prescricoes-resultado-2026-10-12.md`.
