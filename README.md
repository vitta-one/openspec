# Vitta-One

Sistema acadêmico de gerenciamento de clínica médica desenvolvido com **Python + Reflex + PostgreSQL**, seguindo desenvolvimento incremental orientado por especificações com **OpenSpec**.

## Estado atual

A fundação de acesso, o fluxo de paciente/fila, a gestão administrativa de profissionais/especialidades e a agenda por slots explícitos estão implementados nesta branch. A capability consolidada está em `openspec/specs/patient-reception-queue/`, com a evolução correspondente de `openspec/specs/access-control/`. A autorização continua sendo revalidada no servidor em todas as leituras e mutações protegidas.

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
│   ├── patient_queue/
│   ├── professional_directory/
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
export VITTA_ONE_CLINIC_TIMEZONE='America/Sao_Paulo'
# export VITTA_ONE_COOKIE_SECURE='false'      # somente desenvolvimento HTTP local
```

> A duração da sessão não possui valor padrão no projeto. A política definitiva deve ser decidida explicitamente antes de uso real.


### Preview local do Administrador

Para validar o fluxo visual completo durante desenvolvimento local, o Administrador pode habilitar uma navegação unificada de **QA somente leitura**. Esse modo não altera o RBAC de produção e não concede ao Admin as mutações exclusivas de Recepção ou Médico.

PowerShell:

```powershell
$env:VITTA_ONE_LOCAL_ADMIN_PREVIEW="true"
```

CMD:

```cmd
set "VITTA_ONE_LOCAL_ADMIN_PREVIEW=true"
```

Com o flag habilitado e uma sessão `ADMINISTRADOR`, o shell local também expõe:

- `/admin/recepcao`: projeção da fila persistida;
- `/admin/agenda`: projeção somente leitura dos slots e Consultas persistidos;
- `/admin/atendimento`: contexto somente leitura de atendimentos operacionais ativos;
- `/admin/pacientes`: pacientes persistidos + histórico operacional;
- `/admin/financeiro`: estado vazio honesto até a capability financeira existir.

Sem esse flag, as rotas de preview redirecionam para `/admin`.


A sessão do navegador contém somente um identificador opaco e imprevisível. O banco persiste apenas o hash desse token; identidade, role, expiração e revogação são revalidadas no servidor. Nesta versão do Reflex, a implementação usa as opções disponíveis em `rx.Cookie`: `Path=/`, `Max-Age`, `Secure` e `SameSite=Strict`.

As migrações de autenticação, fila de atendimento e diretório profissional estão versionadas em `alembic/versions/` e foram revisadas e validadas contra PostgreSQL 16 descartável. Com `DATABASE_URL` configurada, aplique as migrações antes de criar o primeiro Administrador:

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

## Rotas protegidas

- `/login`: autenticação local, sem cadastro público;
- `/admin`: gestão de especialidades, profissionais e slots explícitos de disponibilidade;
- `/recepcao`: agenda de Consultas + cadastro/localização de pacientes, entrada, reavaliação, retirada e acompanhamento da fila ativa;
- `/medico`: contagem da fila, chamada atômica do próximo paciente e finalização do próprio atendimento ativo;
- `/financeiro`: shell protegido do Financeiro;
- `/acesso-negado`: estado autenticado para tentativa de acesso a uma role incompatível.

Financeiro ainda permanece shell. Administrador executa a gestão do diretório e Recepção/Médico executam a capability de fila; prioridade é sempre informada pela operação (`VERMELHO`, `AMARELO`, `VERDE`) e nunca é calculada ou elevada automaticamente pelo Vitta-One. A autorização é revalidada no backend e não depende apenas de componentes escondidos no frontend.

## Fluxo de desenvolvimento

Mudanças relevantes devem seguir o ciclo:

```text
Contexto → Explore → Propose → Review → Apply → Archive
```

Antes de alterar funcionalidades, leia `AGENTS.md`, `docs/project-overview.md`, `docs/domain-model.md` e `openspec/config.yaml`.
