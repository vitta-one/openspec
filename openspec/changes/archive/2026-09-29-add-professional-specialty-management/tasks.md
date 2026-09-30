## 1. Modelagem e migration

- [x] 1.1 Definir normalização de nomes de especialidade e identificador profissional sem introduzir regra específica de conselho.
- [x] 1.2 Criar modelo `Specialty` com nome, chave normalizada única, `is_active` e timestamps.
- [x] 1.3 Criar modelo `Professional` com nome, identificador profissional único, `is_active`, vínculo opcional/único com `auth_users` e timestamps.
- [x] 1.4 Criar modelo de associação `ProfessionalSpecialty` com FKs e unicidade do par profissional-especialidade.
- [x] 1.5 Registrar os modelos para descoberta do Reflex/Alembic.
- [x] 1.6 Gerar migration incremental sobre `1e98cc2e0552`, revisar `upgrade`/`downgrade` e validar em PostgreSQL 16 descartável.

## 2. Serviços de Especialidade

- [x] 2.1 Implementar criação com normalização e rejeição de nome vazio/duplicado.
- [x] 2.2 Implementar listagem administrativa incluindo estado ativo/inativo.
- [x] 2.3 Implementar edição de nome com tratamento de corrida de unicidade.
- [x] 2.4 Implementar ativação/desativação lógica sem excluir registros.
- [x] 2.5 Garantir que especialidades inativas não sejam aceitas em novas associações.

## 3. Serviços de Profissional

- [x] 3.1 Implementar criação de profissional exigindo nome, identificador único e pelo menos uma especialidade ativa.
- [x] 3.2 Implementar atualização transacional de dados e conjunto de especialidades.
- [x] 3.3 Deduplicar IDs de especialidades recebidos e manter no máximo uma associação por par.
- [x] 3.4 Implementar ativação/desativação lógica preservando associações e vínculo de conta.
- [x] 3.5 Implementar listagem administrativa com especialidades e estado atual.
- [x] 3.6 Implementar vínculo opcional com conta `MEDICO`, rejeitando roles incompatíveis e conta já usada por outro profissional.
- [x] 3.7 Implementar projeção segura de contas Médicas disponíveis sem retornar hashes, tokens ou dados desnecessários.

## 4. Autorização e State Reflex

- [x] 4.1 Criar camada de aplicação que revalide role `ADMINISTRADOR` antes de toda leitura e mutação da capability.
- [x] 4.2 Criar State Reflex do diretório administrativo com loading, empty, error, success e busy state.
- [x] 4.3 Garantir que sessão ausente/expirada ou role incompatível limpe dados carregados e não execute mutações.
- [x] 4.4 Converter erros de validação/unicidade em feedback seguro sem stack trace ou dados sensíveis.

## 5. Interface de Especialidades

- [x] 5.1 Evoluir `/admin` para workspace protegido preservando header/logout e identidade visual existentes.
- [x] 5.2 Criar formulário acessível de nova especialidade com label, validação e prevenção de submissão duplicada.
- [x] 5.3 Exibir lista de especialidades com estado textual ativo/inativo.
- [x] 5.4 Implementar edição de nome e ativação/desativação reversível com feedback acessível.

## 6. Interface de Profissionais

- [x] 6.1 Criar formulário acessível de profissional com nome, identificador, seleção de uma ou mais especialidades e conta Médica opcional.
- [x] 6.2 Exibir diretório de profissionais com especialidades, vínculo de conta e estado ativo/inativo.
- [x] 6.3 Implementar edição de profissional e atualização das associações sem perder estado anterior em caso de erro.
- [x] 6.4 Implementar ativação/desativação reversível.
- [x] 6.5 Garantir layout responsivo, navegação por teclado, foco visível e diferenciação textual de estados.

## 7. Testes e validação

- [x] 7.1 Testar normalização e unicidade de especialidade.
- [x] 7.2 Testar criação/edição de profissional, identificador duplicado, múltiplas especialidades e deduplicação da associação.
- [x] 7.3 Testar rejeição de profissional sem especialidade e de associação com especialidade inativa.
- [x] 7.4 Testar vínculo opcional com conta Médica, role incompatível e unicidade do vínculo.
- [x] 7.5 Testar ativação/desativação preservando associações.
- [x] 7.6 Testar autorização, sessão ausente/expirada e role incompatível.
- [x] 7.7 Executar migration em PostgreSQL descartável, suíte completa, OpenSpec strict e `reflex compile --dry`, corrigindo regressões antes de concluir a change.
