## 1. Modelagem e migration

- [ ] 1.1 Definir normalização de nomes de especialidade e identificador profissional sem introduzir regra específica de conselho.
- [ ] 1.2 Criar modelo `Specialty` com nome, chave normalizada única, `is_active` e timestamps.
- [ ] 1.3 Criar modelo `Professional` com nome, identificador profissional único, `is_active`, vínculo opcional/único com `auth_users` e timestamps.
- [ ] 1.4 Criar modelo de associação `ProfessionalSpecialty` com FKs e unicidade do par profissional-especialidade.
- [ ] 1.5 Registrar os modelos para descoberta do Reflex/Alembic.
- [ ] 1.6 Gerar migration incremental sobre `1e98cc2e0552`, revisar `upgrade`/`downgrade` e validar em PostgreSQL 16 descartável.

## 2. Serviços de Especialidade

- [ ] 2.1 Implementar criação com normalização e rejeição de nome vazio/duplicado.
- [ ] 2.2 Implementar listagem administrativa incluindo estado ativo/inativo.
- [ ] 2.3 Implementar edição de nome com tratamento de corrida de unicidade.
- [ ] 2.4 Implementar ativação/desativação lógica sem excluir registros.
- [ ] 2.5 Garantir que especialidades inativas não sejam aceitas em novas associações.

## 3. Serviços de Profissional

- [ ] 3.1 Implementar criação de profissional exigindo nome, identificador único e pelo menos uma especialidade ativa.
- [ ] 3.2 Implementar atualização transacional de dados e conjunto de especialidades.
- [ ] 3.3 Deduplicar IDs de especialidades recebidos e manter no máximo uma associação por par.
- [ ] 3.4 Implementar ativação/desativação lógica preservando associações e vínculo de conta.
- [ ] 3.5 Implementar listagem administrativa com especialidades e estado atual.
- [ ] 3.6 Implementar vínculo opcional com conta `MEDICO`, rejeitando roles incompatíveis e conta já usada por outro profissional.
- [ ] 3.7 Implementar projeção segura de contas Médicas disponíveis sem retornar hashes, tokens ou dados desnecessários.

## 4. Autorização e State Reflex

- [ ] 4.1 Criar camada de aplicação que revalide role `ADMINISTRADOR` antes de toda leitura e mutação da capability.
- [ ] 4.2 Criar State Reflex do diretório administrativo com loading, empty, error, success e busy state.
- [ ] 4.3 Garantir que sessão ausente/expirada ou role incompatível limpe dados carregados e não execute mutações.
- [ ] 4.4 Converter erros de validação/unicidade em feedback seguro sem stack trace ou dados sensíveis.

## 5. Interface de Especialidades

- [ ] 5.1 Evoluir `/admin` para workspace protegido preservando header/logout e identidade visual existentes.
- [ ] 5.2 Criar formulário acessível de nova especialidade com label, validação e prevenção de submissão duplicada.
- [ ] 5.3 Exibir lista de especialidades com estado textual ativo/inativo.
- [ ] 5.4 Implementar edição de nome e ativação/desativação reversível com feedback acessível.

## 6. Interface de Profissionais

- [ ] 6.1 Criar formulário acessível de profissional com nome, identificador, seleção de uma ou mais especialidades e conta Médica opcional.
- [ ] 6.2 Exibir diretório de profissionais com especialidades, vínculo de conta e estado ativo/inativo.
- [ ] 6.3 Implementar edição de profissional e atualização das associações sem perder estado anterior em caso de erro.
- [ ] 6.4 Implementar ativação/desativação reversível.
- [ ] 6.5 Garantir layout responsivo, navegação por teclado, foco visível e diferenciação textual de estados.

## 7. Testes e validação

- [ ] 7.1 Testar normalização e unicidade de especialidade.
- [ ] 7.2 Testar criação/edição de profissional, identificador duplicado, múltiplas especialidades e deduplicação da associação.
- [ ] 7.3 Testar rejeição de profissional sem especialidade e de associação com especialidade inativa.
- [ ] 7.4 Testar vínculo opcional com conta Médica, role incompatível e unicidade do vínculo.
- [ ] 7.5 Testar ativação/desativação preservando associações.
- [ ] 7.6 Testar autorização, sessão ausente/expirada e role incompatível.
- [ ] 7.7 Executar migration em PostgreSQL descartável, suíte completa, OpenSpec strict e `reflex compile --dry`, corrigindo regressões antes de concluir a change.
