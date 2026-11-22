## 1. Especificação

- [x] 1.1 Definir requisitos da ficha operacional e modal de agendamento.
- [x] 1.2 Preservar contratos de autorização, privacidade e tecnologia.

## 2. Dados e serviços

- [x] 2.1 Implementar projeção autorizada e mascarada de identificação, consultas e fila.
- [x] 2.2 Implementar paginação do histórico e estados sem dados.
- [x] 2.3 Impedir duplicidade de entradas ativas no serviço avulso com bloqueio transacional.

## 3. Interface

- [x] 3.1 Refatorar ficha individual com seções operacionais e ações contextuais.
- [x] 3.2 Reutilizar agendamento em modal na Ficha, Agenda e dashboard, preservando rota antiga.
- [x] 3.3 Fixar paciente da ficha e atualizar consulta após agendamento.

## 4. Verificação e homologação

- [x] 4.1 Adicionar testes de privacidade, autorização, dados persistidos e duplicidade.
- [ ] 4.2 Executar Python/Pytest e OpenSpec strict no ambiente de CI.
- [ ] 4.3 Executar `reflex compile --dry`.
- [ ] 4.4 Verificar modal, foco, responsividade 320/390/768/1024/1440 e regressões em Chromium.
- [ ] 4.5 Revisar resultados da CI e registrar evidências antes de mesclar.
