# Vitta-One

Sistema acadêmico de gerenciamento de clínica médica desenvolvido com **Python + Reflex + PostgreSQL**, seguindo desenvolvimento incremental orientado por especificações com **OpenSpec**.

## Estado atual

A fundação de acesso está integrada: autenticação local, sessão revogável, RBAC, migração inicial e shells protegidos foram validados. A capability consolidada está em `openspec/specs/access-control/`; a próxima evolução funcional será planejada em uma change própria.

## Stack definida

- Reflex como framework full-stack da aplicação web;
- Python;
- PostgreSQL;
- Cloudinary para anexos de exames;
- ZapSign em sandbox para assinatura de prescrições;
- Asaas em sandbox para operações financeiras.

## Estrutura principal

```text
.
├── AGENTS.md
├── DESIGN.md
├── alembic/
├── alembic.ini
├── docs/
│   ├── project-overview.md
│   └── domain-model.md
├── openspec/
│   ├── config.yaml
│   ├── specs/
│   └── changes/
│       └── archive/
├── vitta_one/
│   ├── auth/
│   ├── models/
│   ├── ui/
│   ├── __init__.py
│   └── vitta_one.py
├── tests/
├── assets/
│   └── styles.css
├── rxconfig.py
└── requirements.txt
```

> `vitta_one/` contém a aplicação Reflex. `openspec/` é reservado exclusivamente aos artefatos do OpenSpec.

## Ambiente local no Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

A aplicação exige PostgreSQL. Forneça a conexão somente por variável de ambiente; o projeto normaliza URLs `postgresql://` para o driver Psycopg 3 configurado nas dependências.

```bash
export DATABASE_URL='postgresql+psycopg://<usuario>:<senha>@<host>:5432/<banco>'
```

A duração da sessão é obrigatoriamente explícita e configurada em segundos. O cookie usa `Secure` por padrão; desabilite essa opção apenas em desenvolvimento local sem HTTPS.

```bash
export VITTA_ONE_SESSION_TTL_SECONDS='<segundos-da-sessao>'
export VITTA_ONE_COOKIE_SECURE='true'         # produção/HTTPS
# export VITTA_ONE_COOKIE_SECURE='false'      # somente desenvolvimento HTTP local
```

> A duração da sessão não possui valor padrão no projeto. A política definitiva deve ser decidida explicitamente antes de uso real.

A sessão do navegador contém somente um identificador opaco e imprevisível. O banco persiste apenas o hash desse token; identidade, role, expiração e revogação são revalidadas no servidor. Nesta versão do Reflex, a implementação usa as opções disponíveis em `rx.Cookie`: `Path=/`, `Max-Age`, `Secure` e `SameSite=Strict`.

A migração inicial de autenticação está versionada em `alembic/versions/` e foi revisada e validada contra PostgreSQL 16 descartável. Com `DATABASE_URL` configurada, aplique as migrações antes de criar o primeiro Administrador:

```bash
reflex db migrate
```

O primeiro Administrador pode então ser criado manualmente sem credencial padrão versionada:

```bash
export VITTA_ONE_BOOTSTRAP_ADMIN_EMAIL='admin@exemplo.com'
read -s VITTA_ONE_BOOTSTRAP_ADMIN_PASSWORD
export VITTA_ONE_BOOTSTRAP_ADMIN_PASSWORD
python -m vitta_one.auth.bootstrap
unset VITTA_ONE_BOOTSTRAP_ADMIN_PASSWORD
```

Validações principais:

```bash
python -m pytest -q
reflex compile --dry
```

## Rotas da fundação de acesso

- `/login`: autenticação local, sem cadastro público;
- `/admin`: shell protegido do Administrador;
- `/recepcao`: shell protegido da Recepcionista;
- `/medico`: shell protegido do Médico;
- `/financeiro`: shell protegido do Financeiro;
- `/acesso-negado`: estado autenticado para tentativa de acesso a uma role incompatível.

Esses painéis ainda não contêm módulos de negócio. A autorização é revalidada no backend durante o carregamento das rotas e não depende apenas de componentes escondidos no frontend.

## Fluxo de desenvolvimento

Mudanças relevantes devem seguir o ciclo:

```text
Contexto → Explore → Propose → Review → Apply → Archive
```

Antes de alterar funcionalidades, leia `AGENTS.md`, `docs/project-overview.md`, `docs/domain-model.md` e `openspec/config.yaml`.
