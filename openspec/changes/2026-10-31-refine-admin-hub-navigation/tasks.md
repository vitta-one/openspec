## Implementação
- [x] Compactar a central administrativa com destinos reais e textos corretos.
- [x] Separar na sidebar navegação de administração e ferramentas locais QA.
- [x] Identificar a página administrativa ativa e manter fechamento móvel acessível.
- [x] Acrescentar teste de inventário de links administrativos e QA.

## Validação
- [ ] Executar OpenSpec strict.
- [ ] Executar Pytest e `reflex compile --dry` em ambiente com Python 3.12 e dependências.
- [ ] Homologar navegação por teclado, Escape e gerenciamento de foco do menu móvel.
- [ ] Testar visualmente viewports 320, 390, 768, 1024 e 1440px e ausência de overflow.
- [ ] Validar ambiente de habilitação QA além da flag explícita.
- [ ] Revisar a PR e arquivar esta change somente após todos os gates.
