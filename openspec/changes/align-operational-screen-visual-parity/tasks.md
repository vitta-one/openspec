## 1. Projeções autorizadas

- [x] 1.1 Implementar projeção administrativa agregada com autorização server-side, fuso local e contagens definidas nos specs; verificar zero, limites de dia, inativos e roles negadas em testes.
- [x] 1.2 Implementar projeção de e-mails da agenda para 30 datas locais, agrupando os status especificados e excluindo `SUPPRESSED`; verificar contagens, privacidade e RBAC em testes.

## 2. Painéis e shell

- [x] 2.1 Adicionar state e estados de carregamento/erro ao dashboard administrativo; verificar carregamento protegido no evento da rota `/admin`.
- [x] 2.2 Recriar o dashboard administrativo com quatro métricas reais e atalhos para rotas registradas; verificar links, zero honesto e ausência de valores fixos.
- [x] 2.3 Integrar os indicadores de e-mail no state da Recepção e exibir aceitos, entregues, falhas e pendentes/indeterminados; verificar distinção entre aceito e entregue.
- [x] 2.4 Ajustar o padrão inicial da sidebar por perfil e preservar alternância manual entre rotas do mesmo perfil; verificar shell de Médico, Recepção, Administração, Financeiro e navegação móvel.
- [x] 2.5 Aplicar cabeçalhos e ilustrações SVG decorativas autorais aos shells operacionais, alinhando grid, densidade, tipografia e tokens; verificar que controles permanecem independentes e a arte é ignorada por leitores de tela.
- [x] 2.6 Revisar as 16 rotas existentes sem substituir seus serviços, states, autorização, estados vazios ou ações; executar testes de regressão dos módulos afetados.

## 3. QA visual e documentação

- [x] 3.1 Ajustar o harness de navegador para capturar as 16 rotas em 1768×890 e nas larguras 320, 390, 768, 1024 e 1440; verificar cobertura, títulos e ausência de dados reais.
- [x] 3.2 Comparar capturas do navegador com cada referência local, ajustar divergências de composição e registrar relatório/evidências em `docs/qa/` sem versionar as referências.
- [x] 3.3 Validar foco, teclado, overflow, estados de erro/vazio e `prefers-reduced-motion` nas rotas operacionais; registrar os resultados do Playwright/Chromium.
- [x] 3.4 Atualizar documentação sobre o estado real das integrações Sandbox e limitações de homologação; verificar que instruções e variáveis não contêm credenciais.
- [x] 3.5 Executar OpenSpec strict, pytest, `reflex compile --dry`, `git diff --check` e quality gate aplicável; registrar comandos e corrigir regressões antes de concluir.
