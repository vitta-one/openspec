## Por quê

As 16 telas operacionais já implementadas divergem em composição, densidade e alinhamento das referências visuais aprovadas. A correção precisa preservar os fluxos atuais, as permissões por role e a representação fiel dos dados persistidos, enquanto torna as diferenças verificáveis por capturas comparáveis.

## O que muda

- Ajustar o shell compartilhado e as 16 páginas para reproduzir a geometria e a hierarquia das referências dentro das limitações reais de viewport e renderização.
- Corrigir problemas de responsividade e acessibilidade encontrados nas páginas alteradas sem remover ações funcionais.
- Preparar captura visual isolada com dados sintéticos de QA, comparações por rota e evidências separadas para desktop e viewports adicionais.
- Documentar diferenças de dados e limitações de renderização sem tratar exemplos das imagens como dados reais.

Fora do escopo: novas integrações, funcionalidades de negócio, mudanças de RBAC, modelos, migrações, alterações em produção, merge e deploy.

## Capabilities

### Novas capabilities

Nenhuma.

### Capabilities modificadas

- `reception-operational-dashboard`: incluir na visão do dia a contagem persistida de consultas canceladas.

## Impacto

- Shell, CSS e componentes Reflex das páginas de Recepção, Administração, Financeiro e Médico.
- Ferramentas e documentação de QA visual, usando exclusivamente PostgreSQL descartável com dados sintéticos.
- Preservação dos contratos e autorização existentes; nenhuma dependência, integração externa, modelo ou migration nova é prevista. A projeção do dashboard da Recepção ganha uma contagem SQL de consultas canceladas para informar o card real da referência.
