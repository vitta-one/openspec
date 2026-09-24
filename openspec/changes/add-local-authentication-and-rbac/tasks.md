## 1. Banco e dependências de autenticação

- [x] 1.1 Habilitar as dependências de banco suportadas pelo Reflex e configurar PostgreSQL por variável de ambiente, sem credenciais versionadas.
- [x] 1.2 Selecionar e fixar uma biblioteca segura e compatível com Python 3.12 para password hashing, preferencialmente Argon2id.
- [x] 1.3 Criar os modelos persistentes mínimos de usuário e sessão sem antecipar campos dos módulos clínicos.
- [ ] 1.4 Inicializar/ajustar Alembic pelo fluxo do Reflex, gerar a migração e revisar o script antes de aplicá-lo.

## 2. Serviço de identidade e sessão

- [x] 2.1 Implementar normalização e busca do e-mail de login com unicidade garantida no banco.
- [x] 2.2 Implementar criação/verificação segura do hash de senha sem registrar credenciais em logs.
- [x] 2.3 Implementar criação de sessão opaca, imprevisível, expirada/revogável e associada ao usuário no servidor.
- [x] 2.4 Implementar resolução do usuário autenticado a partir da sessão e invalidação no logout.
- [x] 2.5 Implementar mecanismo manual e idempotente de bootstrap do primeiro Administrador sem senha padrão hardcoded.

## 3. Autenticação no Reflex

- [ ] 3.1 Criar State de autenticação com login, restauração de sessão e logout seguindo os mecanismos atuais do Reflex.
- [ ] 3.2 Criar página/formulário acessível de login com validação de campos, estados de envio e mensagem genérica para credenciais inválidas.
- [ ] 3.3 Configurar armazenamento cliente apenas para o identificador de sessão necessário, usando as opções de segurança disponíveis e sem expor dados sensíveis.
- [ ] 3.4 Garantir que páginas e dados protegidos não sejam renderizados/carregados para sessão ausente, inválida ou expirada.

## 4. RBAC e shells protegidos

- [x] 4.1 Definir as quatro roles do domínio como conjunto fechado: Administrador, Recepcionista, Médico e Financeiro.
- [ ] 4.2 Criar abstração reutilizável de autorização server-side para sessão autenticada e role requerida.
- [ ] 4.3 Criar shells mínimos e responsivos dos quatro painéis, sem implementar módulos de negócio antecipadamente.
- [ ] 4.4 Redirecionar após login para o shell correspondente à role e rejeitar acesso direto a shell incompatível.
- [ ] 4.5 Validar autorização também em event handlers/loaders protegidos, independentemente do estado visual da interface.

## 5. Verificação e qualidade

- [ ] 5.1 Adicionar testes para login válido, e-mail inexistente, senha inválida, logout, sessão ausente, sessão expirada e sessão revogada.
- [ ] 5.2 Adicionar testes para cada role e para tentativa de acesso direto a painel/operação sem permissão.
- [ ] 5.3 Testar bootstrap repetido e garantir que não cria usuário duplicado nem sobrescreve credencial existente.
- [ ] 5.4 Verificar que senha em texto puro, hash de senha e identificadores sensíveis não aparecem em logs ou respostas de erro.
- [ ] 5.5 Validar teclado, foco visível, labels, mensagens de erro e contraste da tela de login, além dos estados loading/erro/sucesso relevantes.
- [ ] 5.6 Executar a suíte de testes aplicável e `reflex compile --dry`, corrigindo regressões antes de marcar a change como pronta para archive.
