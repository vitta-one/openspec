# Proposal — Navegação global hierárquica e acessível

## Motivação
O shell atual apresenta links administrativos sem hierarquia, recolhimento desktop que remove a sidebar completamente e drawer mobile sem gestão explícita de foco/Escape. Há risco de confusão entre visualizações locais de QA e responsabilidades administrativas.

## Escopo
- Reutilizar `vitta_one/ui/components.py` e tokens de `assets/styles.css`.
- Agrupar visualizações QA separadamente das tarefas de Administração.
- Preservar item ativo em subpáginas, com distinção entre item atual e ancestral.
- Implementar trilho compacto no desktop; drawer temporário com foco, Escape e bloqueio de rolagem no mobile.
- Identificar área no header e conta/logout somente na sidebar, sem ampliar permissões.

## Fora de escopo
Alterar rotas, RBAC, dados clínicos, arquitetura Reflex, migrações ou integrações.

## Risco e mitigação
Mudanças no shell compartilhado afetam cinco perfis. Exercitar montagem dos componentes, compilação Reflex, testes de navegação e Playwright em viewports de 320/390/768/1024/1440 px antes do merge.
