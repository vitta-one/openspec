## 1. Dados e projeções
- [ ] 1.1 Agrupar contagens de consultas e fila em duas consultas agregadas preservando os filtros e o dia clínico.
- [ ] 1.2 Adicionar até cinco pendências elegíveis ordenadas por horário e manter a contagem total.
- [ ] 1.3 Propagar os registros e situação operacional por tipos/snapshot sem incluir dados clínicos.

## 2. Dashboard e estados
- [ ] 2.1 Exibir seis KPIs, suas definições temporais e links para os módulos atuais.
- [ ] 2.2 Mostrar situação e acesso à Agenda nas próximas consultas.
- [ ] 2.3 Criar seção de pendências com total, limite visível e estado vazio, sem inferir falta.
- [ ] 2.4 Diferenciar loading inicial, snapshot carregado, refresh e falha com nova tentativa.
- [ ] 2.5 Garantir quebra de linha e foco visível para cards/linhas responsivos.

## 3. Especificação e qualidade
- [ ] 3.1 Registrar a auditoria da Recepção e atualizar UX-CONTRACT e spec consolidada/delta.
- [ ] 3.2 Testar contagens, timezone, status, limite/ordem das pendências e ausência de conteúdo clínico.
- [ ] 3.3 Verificar o número de consultas SQL e executar pytest, Reflex compile e OpenSpec validate.
- [ ] 3.4 Executar QA Chromium disponível, corrigir falhas e abrir PR para develop sem merge.
