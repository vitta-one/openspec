# Encerramento do ciclo OpenSpec — Innovation Lab

Data: 22/11/2026. Repositório: `vitta-one/openspec`. Branch: `docs/openspec-capability-coverage-20261122`. PR: [#360](https://github.com/vitta-one/openspec/pull/360).

## Escopo da operação

Por decisão explícita do responsável pelo projeto, todas as **26 changes previamente ativas** foram movidas, sem reescrever o conteúdo, para `openspec/changes/archive/`. O prefixo de data original foi preservado em nomes já datados; as demais receberam `2026-11-22-`. O total do histórico após essa alteração é **45 changes arquivadas**. Os 25 contratos antes consolidados foram posteriormente congelados num snapshot histórico, conforme adendo abaixo.

Os dois projetos de integração propostos somente para planejamento nesta PR foram **retirados do escopo acadêmico** e seus artefatos de change não integram o resultado final. Esta alteração não adiciona feature, migration nem deploy.

## Advertências e rastreabilidade

O arquivo `tasks.md` de cada change foi preservado inclusive com itens ainda desmarcados. **O arquivamento é uma decisão de encerramento de escopo e não equivale a comprovação de 100% das tarefas executadas**, de homologação real de provedor, nem de equivalência visual integral.

O histórico anterior inclui registros de testes e componentes já presentes na `develop`, mas a fotografia de código é a fonte prioritária sobre intenções. Revisões de integração externa e acessibilidade devem usar evidências próprias antes de uso real.

## Procedimento de QA

- Verificar que não restam diretórios ativos de change neste corte e que os 26 foram preservados no archive.
- Executar OpenSpec strict em CI.
- Executar Pytest, migration QA PostgreSQL 16 e Reflex compile, com smoke HTTP de build quando disponível.
- Não marcar tarefas historicamente pendentes como feitas, não usar credenciais reais e não executar merge/deploy sem autorização.

## Evidências

- [Catálogo e rastreabilidade](openspec-capability-catalog-2026-11-22.md)
- [PR da regularização](https://github.com/vitta-one/openspec/pull/360)

## Adendo: congelamento das 25 specs (22/11/2026)

Por solicitação expressa para a apresentação acadêmica, os **25 diretórios de specs** foram movidos, com hashes de árvore Git preservados, de `openspec/specs/<capability>/` para `docs/archive/openspec-specs-2026-11-22/<capability>/`. A pasta `openspec/specs/` fica apenas com `.gitkeep`; as 45 changes continuam em `openspec/changes/archive/`. Nenhum contrato foi descartado.

**Isto não é o comportamento convencional de `openspec archive`**: a partir de agora o checkout não tem specs canônicas ativas. Para continuar desenvolvimento orientado por especificações, será necessário restaurar e revisar os contratos. O teste e o OpenSpec strict validam a cópia histórica em diretório temporário, sem repovoar `openspec/specs/` no GitHub. O arquivamento não comprova tarefas históricas pendentes nem homologação externa.
