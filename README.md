# Vitta-One

Sistema acadêmico de gerenciamento de clínica médica desenvolvido com **Python + Reflex + PostgreSQL**, seguindo desenvolvimento incremental orientado por especificações com **OpenSpec**.

## Estado atual

O repositório está na fase de fundação. A change `add-local-authentication-and-rbac` está em implementação para estabelecer autenticação local, sessão revogável e as quatro roles do domínio antes dos módulos clínicos e financeiros.

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
│   ├── __init__.py
│   └── vitta_one.py
├── tests/
├── assets/
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

A migração da change de autenticação ainda deve ser gerada e revisada pelo fluxo do Reflex antes de aplicar o schema em um banco. Depois disso, o primeiro Administrador poderá ser criado manualmente sem credencial padrão versionada:

```bash
export VITTA_ONE_BOOTSTRAP_ADMIN_EMAIL='admin@exemplo.com'
read -s VITTA_ONE_BOOTSTRAP_ADMIN_PASSWORD
export VITTA_ONE_BOOTSTRAP_ADMIN_PASSWORD
python -m vitta_one.auth.bootstrap
unset VITTA_ONE_BOOTSTRAP_ADMIN_PASSWORD
```

Validação rápida do Reflex:

```bash
reflex compile --dry
```

## Fluxo de desenvolvimento

Mudanças relevantes devem seguir o ciclo:

```text
Contexto → Explore → Propose → Review → Apply → Archive
```

Antes de alterar funcionalidades, leia `AGENTS.md`, `docs/project-overview.md`, `docs/domain-model.md` e `openspec/config.yaml`.
