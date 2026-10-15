## 1. Dados e projeções
- [x] 1.1 Agrupar contagens de consultas e fila em duas consultas agregadas preservando os filtros e o dia clínico.
- [x] 1.2 Adicionar até cinco pendências elegíveis ordenadas por horário e manter a contagem total.
- [x] 1.3 Propagar os registros e situação operacional por tipos/snapshot sem incluir dados clínicos.

## 2. Dashboard e estados
- [x] 2.1 Exibir seis KPIs, suas definições temporais e links para os módulos atuais.
- [x] 2.2 Mostrar situação e acesso à Agenda nas próximas consultas.
- [x] 2.3 Criar seção de pendências com total, limite visível e estado vazio, sem inferir falta.
- [x] 2.4 Diferenciar loading inicial, snapshot carregado, refresh e falha com nova tentativa.
- [x] 2.5 Garantir quebra de linha e foco visível para cards/linhas responsivos.

## 3. Especificação e qualidade
- [x] 3.1 Registrar a auditoria da Recepção e atualizar UX-CONTRACT e spec consolidada/delta.
- [x] 3.2 Testar contagens, timezone, status, limite/ordem das pendências e ausência de conteúdo clínico.
- [x] 3.3 Verificar o número de consultas SQL e executar pytest, Reflex compile e OpenSpec validate.
- [x] 3.4 Executar QA Chromium disponível, corrigir falhas e abrir PR para develop sem merge.


## Evidências de verificação

- `npx -y @fission-ai/openspec@1.13.0 validate --all --strict --no-interactive`: 9 itens aprovados.
- `python -m pytest -q`: 186 testes aprovados; 1 aviso SQLAlchemy em teste de onboarding médico.
- `reflex compile --dry`: compilação aprovada.
- QA Chromium: 18 testes aprovados; dashboard exercitado por teclado e em viewports 320, 375 e 768.
- QA PostgreSQL e navegador usaram infraestrutura descartável e dados sintéticos. Nenhum modelo ou migration foi adicionado.
