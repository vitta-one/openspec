## Diretório e filtros
- [x] Reutilizar filtros e paginação reais no State sem novos endpoints REST.
- [x] Converter listagem em tabela semântica desktop e lista compacta mobile.
- [x] Acrescentar estado de resultado vazio, limpeza dos filtros e retry de erro de carga.
- [x] Reutilizar modal de edição e formulário de especialidades opcionais.

## Segurança e operações
- [x] Diferenciar estado de acesso de status profissional sem simular entrega.
- [x] Contextualizar reemissão de credenciais e tratar erro de transporte.
- [x] Confirmar mudança de situação e rejeitar confirmação obsoleta no servidor.
- [x] Preservar cadastro de profissional, conta e relações existentes.

## Contratos e testes
- [x] Criar delta OpenSpec da regra de especialidades opcionais.
- [x] Atualizar testes de cadastro e edição sem especialidades.
- [x] Testar conflito de status esperado no serviço.
- [ ] Executar OpenSpec strict e Pytest completo.
- [ ] Executar `reflex compile --dry` e testes Chromium.
- [ ] Homologar responsividade 320/390/768/1024/1440, teclado e foco.
- [ ] Revisar CI, efetuar correções e somente depois considerar archive/merge.
