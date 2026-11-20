## Contexto

Ver proposta em `proposal.md`. O produto usa páginas Reflex server-side e um shell comum com navegação distinta por role. Já há testes e capturas anteriores, mas as capturas atuais não foram comparadas às referências; parte dos dados de QA também não corresponde aos estados exibidos nos PNGs. A aplicação deve continuar usando suas projeções e autorização existentes.

## Objetivos / Não objetivos

**Objetivos:**
- Corrigir primeiro a geometria compartilhada do shell e depois as composições específicas das 16 rotas.
- Acrescentar à projeção autorizada da Recepção uma contagem diária de consultas canceladas, sem alterar a definição das consultas ativas nem expor dados pessoais.
- Capturar as seis dimensões previstas usando uma base PostgreSQL descartável e contas/registros explicitamente sintéticos.
- Comparar cada captura desktop ao PNG aprovado sem distorcer a referência 01; documentar separadamente diferenças de estado/dados e diferenças de renderização.
- Verificar comportamento e acessibilidade das áreas tocadas, sem reduzir os controles funcionais existentes.

**Não objetivos:**
- Criar registros demonstrativos em produção, acrescentar integrações, alterar regras de domínio, RBAC, sessões, API, modelos ou migrations.
- Fazer merge, deploy ou editar qualquer base além do contêiner descartável de QA.
- Tratar métricas de similaridade de pixels como prova isolada de paridade.

## Decisões

1. **Manter Reflex, componentes e tokens existentes.** Ajustes ficam no shell, CSS e componentes Reflex responsáveis pelas rotas. Isso preserva o fluxo server-side e evita uma camada de UI paralela. Uma reescrita de páginas ou novo framework aumentaria o risco funcional sem contribuir com as correções localizadas.
2. **Usar dados reais da base descartável e separar conteúdo de composição.** A fixture de comparação conterá somente contas e dados sintéticos; rotas cujo alvo representa estado vazio serão capturadas sem registros correspondentes. Valores ilustrativos não serão introduzidos nos serviços/projeções da aplicação. Se o desenho depender de uma integração não configurada, o relatório registrará a limitação.
3. **Derivar o card de cancelamentos na mesma projeção protegida.** A consulta do dashboard já agrega estados persistidos por dia local; o novo valor será uma contagem condicional no mesmo SELECT e seguirá a autorização da Recepção. Criar números na UI ou uma nova chamada independente aumentaria risco de inconsistência.
4. **Comparar quadros sem redimensionamento não uniforme.** Capturas desktop e referência serão colocadas em quadros de comparação; a referência 01 será alinhada com preservação de aspecto e margens neutras. Gerar lado a lado, overlay e diff, além de registrar a medida de viewport, sem mascarar conteúdo estrutural.
5. **Separar evidência por finalidade.** Manifestos distintos identificarão capturas, verificações funcionais e avaliações visuais; capturas e artefatos de diff permanecem ignorados pelo Git. O relatório versionado traz métricas, caminhos das evidências locais e limitações, não imagens com dados de usuário.
6. **Tratar referências móveis como expectativa de reflow.** As referências fornecidas são desktop. Nos outros cinco viewports serão avaliados reflow, acesso às ações, overflow local de tabelas, foco, drawer e legibilidade; não será alegada equivalência pixel a pixel com uma referência mobile inexistente.

## Riscos / trade-offs

- **Diferenças de conteúdo persistido alteram a aparência de telas dependentes de dados** → Capturar com fixture sintética controlada; separar as diferenças semânticas das de layout e não ocultar registros reais.
- **Mudanças globais podem afetar páginas fora das 16 rotas** → Preferir seletores de shell/componentes já existentes e executar regressão de rotas, testes e compilação.
- **Fontes e rasterização variam entre ambientes** → Fixar viewport e navegador no runner, registrar ambiente e não interpretar pequenas diferenças de antialiasing como defeitos geométricos.
- **Capturas clínicas podem expor dados sensíveis** → Usar apenas o banco descartável local, evitar exportar logs/artefatos com dados pessoais e validar a origem da URL antes de capturar.

## Plano de migração

Não há migração de dados nem implantação. A reversão é feita revertendo os commits da branch. O banco local de QA usa contêiner temporário com `--rm`; ao encerrar a execução, o contêiner será parado e removido.
