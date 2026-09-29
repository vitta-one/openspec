## Context

O projeto está em estado greenfield, com Reflex 0.9.10.post2, Python e PostgreSQL definidos como stack. Existe somente a página padrão do Reflex e ainda não há modelos de banco, autenticação ou funcionalidades de domínio implementadas. Os requisitos globais já definem quatro roles e exigem que autorização seja aplicada no lado servidor.

A documentação atual do Reflex recomenda manter tokens e informações sensíveis em variáveis backend-only e validar sessão/permissões em cada event handler ou carregamento que acesse dados privados. Reflex também oferece integração nativa com SQLModel/SQLAlchemy por `rx.Model`, sessões de banco por `rx.session()` e migrações via Alembic.

## Goals / Non-Goals

**Goals:**

- criar uma base local de identidade sem depender de provedor externo;
- autenticar usuários por e-mail e senha;
- persistir usuários e sessões no PostgreSQL;
- garantir que autorização não dependa apenas de componentes escondidos ou redirects;
- oferecer login, logout e restauração de sessão;
- representar as quatro roles fixas do domínio;
- criar shells mínimos de dashboard para validar roteamento e autorização;
- fornecer bootstrap seguro e repetível do primeiro Administrador;
- manter a solução pequena o bastante para servir de fundação às próximas changes.

**Non-Goals:**

- cadastro público de usuários;
- recuperação ou redefinição de senha;
- MFA;
- OAuth, login social ou provedores externos;
- gestão administrativa completa de usuários;
- definição detalhada das permissões internas de cada módulo futuro;
- pacientes, profissionais, agenda, consultas, atendimento, prontuário, exames, prescrições, financeiro ou dashboards funcionais;
- Cloudinary, ZapSign ou Asaas nesta change.

## Decisions

### 1. Autenticação local com PostgreSQL

A identidade será armazenada no banco definido pelo projeto. O modelo inicial de usuário deve conter apenas os campos necessários para autenticação e autorização desta change, evitando antecipar atributos de módulos futuros.

O e-mail será o identificador de login inicial e deverá ser tratado como único de forma normalizada. Essa é uma decisão da Change 001 e pode ser revisada por uma change futura antes de existirem integrações externas dependentes dela.

### 2. Persistência usando recursos nativos do Reflex

Usar `rx.Model`/SQLModel para os modelos persistentes, `rx.session()` para transações e o fluxo de migração suportado pelo Reflex/Alembic. Não introduzir um ORM paralelo nesta etapa.

A conexão PostgreSQL será fornecida por configuração de ambiente; nenhuma URL com credenciais será versionada.

### 3. Hash de senha com algoritmo próprio para password hashing

Senhas nunca serão criptografadas de forma reversível nem processadas com hash genérico como SHA-256 puro. A implementação deverá selecionar uma biblioteca mantida e compatível com Python 3.12 que ofereça algoritmo apropriado para password hashing, preferencialmente Argon2id, com parâmetros seguros e salt automático.

A biblioteca concreta será fixada durante o apply após verificação de compatibilidade e adicionada explicitamente às dependências.

### 4. Sessão revogável no servidor

Preferir sessão opaca e revogável em vez de usar a role ou a identidade como informação confiável vinda do navegador. O cliente manterá apenas um identificador de sessão imprevisível; os dados de identidade, role, validade e revogação permanecem no servidor/banco.

A sessão terá expiração configurável. Logout revoga a sessão atual. O cookie/storage utilizado pelo Reflex deve receber as opções de segurança disponíveis adequadas ao ambiente; em produção, comunicação segura deve ser exigida.

Não armazenar senha, hash de senha ou informações clínicas em storage do navegador.

### 5. Autorização centralizada e reaplicada nos handlers

Criar uma camada reutilizável para obter o usuário autenticado e exigir uma sessão/role antes de executar operações protegidas. Cada State/event handler futuro que acesse dados privados deverá chamar essa validação ou utilizar a abstração equivalente definida nesta change.

A proteção de rota e o redirecionamento visual existem para UX, mas nunca substituem a validação server-side.

### 6. Roles como conjunto fechado nesta etapa

As roles reconhecidas serão `ADMINISTRADOR`, `RECEPCIONISTA`, `MEDICO` e `FINANCEIRO`, apresentadas na interface em português. Não criar tabela de permissões finas ou role dinâmica nesta change porque os requisitos atuais definem RBAC simples.

### 7. Dashboard inicial como shell, não módulo funcional

Após login, a aplicação direcionará para um shell mínimo de painel conforme a role. Esses shells servem para provar autenticação, roteamento e autorização e não devem antecipar cards, métricas ou funcionalidades que pertencem às changes futuras.

### 8. Bootstrap sem credencial padrão

O primeiro Administrador será criado por mecanismo executado manualmente e de forma idempotente. E-mail e senha devem ser fornecidos por entrada segura/configuração de ambiente no momento da execução. O mecanismo deve recusar duplicação e nunca conter senha padrão no repositório.

### 9. Tratamento de falhas de autenticação

Falhas de login devem retornar mensagem genérica, sem diferenciar e-mail inexistente de senha incorreta. Exceções internas e dados sensíveis não devem aparecer para o usuário nem em logs desnecessários.

Rate limiting, bloqueio progressivo e MFA são reconhecidos como hardening importante, mas ficam fora desta primeira capability para evitar introduzir infraestrutura adicional antes dos fluxos básicos estarem consolidados.

## Risks / Trade-offs

- **Autenticação customizada aumenta responsabilidade de segurança:** mitigado mantendo escopo pequeno, usando password hashing estabelecido e autorização server-side em todas as operações protegidas.
- **Sessão persistida adiciona modelo e limpeza de dados expirados:** em troca, logout e revogação ficam explícitos e não dependem apenas da validade de um token auto-contido.
- **E-mail como identificador pode precisar mudar:** a decisão fica isolada na capability de acesso e pode ser modificada por change futura.
- **Ausência de recuperação de senha:** aceitável nesta etapa porque não há cadastro público e o objetivo é estabelecer a fundação; deve ser tratado antes de uso real fora do ambiente acadêmico.
- **Sem rate limiting nesta change:** adequado ao escopo acadêmico inicial, mas não deve ser interpretado como suficiente para produção pública.
- **Roteamento por role ainda não define permissões granulares:** deliberado; permissões detalhadas serão especificadas junto aos módulos que realmente as utilizam.
