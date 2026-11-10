## 1. Contratos, modelos e migração

- [x] 1.1 Criar enums e modelos de anexos, assinatura, financeiro, auditoria e webhooks com constraints/índices; verificar testes de metadata e importação dos modelos.
- [ ] 1.2 Criar migration Alembic aditiva para todas as tabelas novas; verificar upgrade, downgrade e novo upgrade em PostgreSQL QA isolado.
- [ ] 1.3 Atualizar exportação/descoberta de modelos no Reflex e confirmar `reflex compile --dry`.

## 2. Exames e Cloudinary

- [x] 2.1 Implementar configuração e cliente Cloudinary com assinatura server-side, timeout e erros sanitizados; verificar testes HTTP sem rede.
- [x] 2.2 Implementar validação, upload, listagem, liberação, download temporário e exclusão auditável; verificar casos válidos, formato/tamanho inválido, indisponibilidade e retry.
- [x] 2.3 Implementar autorização por Paciente/Consulta/Médico e projeções para prontuário e portal; verificar IDOR, role negada e documento não liberado.
- [ ] 2.4 Adicionar UI Reflex de anexos com loading/vazio/erro/sucesso, upload acessível e responsivo; verificar compile e testes de componentes.

## 3. Assinatura de prescrições e ZapSign

- [x] 3.1 Implementar configuração e cliente ZapSign para criar, consultar e obter documento, com timeout e erros sanitizados; verificar testes HTTP sem rede.
- [x] 3.2 Implementar solicitação idempotente, estados, reconciliação segura sem retry cego e bloqueio de mutações após envio; verificar concorrência e repetição.
- [x] 3.3 Implementar webhook autenticado/idempotente com transições monotônicas; verificar token inválido, payload inválido, reentrega e evento fora de ordem.
- [ ] 3.4 Atualizar impressão e UI Médica/portal para estado e acesso protegido ao documento final; verificar ausência de selo falso e foco/teclado.

## 4. Financeiro e Asaas Sandbox

- [x] 4.1 Implementar catálogo, contas, itens, pagamentos e cálculos em centavos com autorização Financeiro; verificar validação, histórico e totais server-side.
- [x] 4.2 Implementar configuração e cliente Asaas para cliente, cobrança, consulta e cancelamento em Sandbox; verificar headers, base URL, timeout e erros sem rede.
- [x] 4.3 Implementar emissão idempotente, reconciliação e webhook autenticado/idempotente; verificar retries, evento duplicado e pagamento único.
- [ ] 4.4 Substituir shell Financeiro por dashboard/listas/formulários com dados persistidos e estados completos; verificar filtros, vazio e responsividade.
- [x] 4.5 Expor somente contas próprias e links hospedados no portal do Paciente; verificar IDOR e ausência de dados brutos de cartão.

## 5. Segurança, integração e documentação

- [x] 5.1 Unificar rotas ASGI de ativação e webhooks com limites de body, JSON estrito e headers seguros; verificar respostas genéricas e `no-store`.
- [x] 5.2 Documentar variáveis, setup Sandbox, webhooks, diagnóstico e comportamento sem credenciais no README/guia; verificar que nenhum segredo real foi versionado.
- [x] 5.3 Atualizar visão de arquitetura/domínio e relatório de homologação com distinção entre local, mock e Sandbox; verificar links e comandos.
- [x] 5.4 Auditar logs, mensagens e persistência para segredos/PII; verificar busca automatizada e testes de erro sanitizado.

## 6. Verificação e entrega

- [ ] 6.1 Validar OpenSpec strict e executar suíte Pytest unitária/autorização/integração simulada; registrar contagens e resultados.
- [ ] 6.2 Executar testes PostgreSQL de constraints, idempotência e concorrência em QA isolado; registrar indisponibilidade quando o ambiente não fornecer banco.
- [ ] 6.3 Executar `reflex compile --dry` e QA Chromium das jornadas críticas em 320, 375, 768 e 1280 px; registrar evidências ou bloqueio ambiental.
- [ ] 6.4 Revisar diff, status, segurança e regressões; criar commits claros e abrir PR contra `develop` sem merge/deploy.
