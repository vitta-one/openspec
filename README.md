# Vitta-One

Sistema acadêmico de gerenciamento de clínica médica desenvolvido com **Python + Reflex + PostgreSQL**, seguindo desenvolvimento incremental orientado por especificações com **OpenSpec**.

## Estado atual

A fundação de acesso, paciente/fila, profissionais/especialidades, agenda, lifecycle da Consulta, registro clínico e Prescrições estruturadas estão implementados. Os contratos normativos das sete capabilities estão consolidados sob `openspec/specs/`, e as evoluções concluídas estão preservadas em `openspec/changes/archive/`. A autorização continua sendo revalidada no servidor em todas as leituras e mutações protegidas. A validação de Prescrições inclui testes PostgreSQL, suíte Python e navegador Chromium automatizado; homologação presencial em dispositivos físicos continua recomendada antes de uso real.

## Stack definida

- Reflex como framework full-stack da aplicação web;
- Python;
- PostgreSQL;
- Cloudinary para anexos de exames;
- ZapSign em sandbox para assinatura de prescrições (integração planejada; ainda não aplicada nesta capability);
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

## Início rápido para desenvolvimento local — Docker + um comando

Este é o caminho recomendado para **testar a aplicação no próprio computador**.
O Docker Compose inicia apenas o **PostgreSQL 16**; o **Reflex roda no host**,
com hot reload. Isso evita rebuild do frontend a cada alteração e permite
iniciar o conjunto com `make dev` em execuções seguintes.

**Pré-requisitos:** Docker com Compose V2 (`docker compose version`), Python
3.12, Git e Make. Tenha Node.js disponível conforme o setup Reflex descrito
abaixo. No Linux, seu usuário precisa conseguir usar `docker info` sem erro.

Se ainda não clonou, clone a branch disponível para testes:

~~~bash
git clone --branch feat/admin-ux-contrast-navigation \
  git@github.com:vitta-one/openspec.git
cd openspec
~~~

Se já clonou o repositório, preserve alterações locais antes de trocar de
branch. Para obter a versão da PR #323:

~~~bash
cd ~/Documents/openspec
git fetch origin
git switch feat/admin-ux-contrast-navigation
git pull --ff-only
~~~

Na **primeira utilização**, cadastre uma conta de Administrador, com e-mail e
senha escolhidos na hora (a senha **não aparece no terminal**):

~~~bash
make admin
~~~

Depois, **sempre que for desenvolver/testar**, basta:

~~~bash
make dev
~~~

Abra **http://localhost:3000/login**. O script:

- cria `.env.docker` local com senha aleatória protegida por permissões `600`;
- inicia um **PostgreSQL 16** via `compose.dev.yaml` e aguarda o banco ficar pronto;
- configura o banco `vitta_one_qa` em `127.0.0.1:5433` para não conflitar com
  um PostgreSQL nativo em `5432`;
- cria `.venv` Python 3.12 e instala dependências **somente na primeira execução
  ou quando `requirements*.txt` mudarem**;
- aplica `reflex db migrate` apenas nesse banco QA local;
- inicia `reflex run --env dev`, com hot reload.

Atalhos adicionais:

| Comando | Ação |
| --- | --- |
| `make dev` | Inicia o banco e o Reflex em modo desenvolvimento |
| `make admin` | Cria o primeiro administrador, preservando o existente |
| `make db-only` | Inicia só o banco PostgreSQL |
| `make db-status` | Exibe status do contêiner |
| `make db-logs` | Acompanha logs do banco |
| `make db-stop` | Para o banco sem excluir os dados |

**Para parar o Reflex**, use `Ctrl+C` no terminal de `make dev`. O PostgreSQL
continua ativo e seu volume `vitta_one_dev_pgdata` **não é removido**.
Se não tiver Make, use `bash scripts/dev-local.sh dev` (ou `admin`).

**Segurança:** o Compose escuta somente em `127.0.0.1:5433`; as credenciais
locais ficam em `.env.docker`, ignorado pelo Git. Nunca rode
`docker compose down -v` nem apague o volume para "reiniciar" o ambiente:
isso destruiria seus dados locais. Se `.env.docker` for perdido e o volume ainda
existir, o script recusa recriar credenciais em vez de alterar o banco existente.
Não use dados reais de pacientes e não execute os seeds descartáveis do CI
nessa instância persistente.

A seção seguinte documenta o setup **manual/legado** para ambientes que não
usam Docker, além dos procedimentos completos de QA e validação.

## Instalação e setup completo — do zero até o QA

Este roteiro é a referência oficial para rodar o projeto, tanto numa máquina nova quanto depois de novos merges. **Execute os comandos a partir da raiz `openspec/`.** Use apenas dados sintéticos no ambiente de QA.

### 1. Pré-requisitos e versões

| Ferramenta | Requisito | Para quê |
| --- | --- | --- |
| Git | Instalado | Clonar/atualizar o repositório |
| Python | **3.12.x** | Runtime e venv; não use Python 3.9 do macOS |
| PostgreSQL | **16.x** | Persistência local |
| Node.js + npx | Instalados | Compilação Reflex/OpenSpec |
| pip, venv | Incluídos no Python | Dependências Python |
| Homebrew/Docker | **Opcionais** | Não necessários para o Hackintosh |
| Resend | **Opcional** | Enviar credenciais temporárias por e-mail |
| Cloudinary/ZapSign/Asaas | Não necessários | Integrações planejadas para outra etapa |

Comandos de inspeção no macOS/Linux:

~~~bash
git --version
python3.12 --version
node --version
npx --version
~~~

No Windows, verifique `py -3.12 --version`, `git --version`, `node --version` e `npx --version`. O projeto fixa `reflex[db]==0.9.10.post2` em `requirements.txt`. **Não execute `pip install --upgrade reflex` sem uma mudança planejada e testada.**

### 2. Clonar o projeto (primeiro acesso) ou atualizar (já clonado)

Para criar uma cópia em `~/Documents/openspec` no macOS/Linux:

~~~bash
cd ~/Documents
git clone --branch develop https://github.com/vitta-one/openspec.git
cd openspec
git status --short
~~~

A URL SSH `git@github.com:vitta-one/openspec.git` também funciona se sua conta estiver configurada. É necessário ter permissão para acessar o repositório.

Se a pasta **já existe**, **não clone de novo**:

~~~bash
cd ~/Documents/openspec
git status --short
git fetch origin
git switch develop
git pull --ff-only
~~~

**Antes de trocar de branch, preserve qualquer modificação local** (commit ou stash identificado). Não use `git reset --hard` ou `git clean -fd` para "resolver" o setup.

### 3. macOS / Hackintosh (Intel ou AMD) sem Homebrew e sem Docker

Este fluxo usa instaladores oficiais e comandos de Terminal. Os binários são universais para macOS x86_64/arm64, mas **Hackintosh não possui suporte oficial dos fornecedores**; primeiro confirme que funcionam no seu processador.

**3.1. Ferramentas de compilação**

~~~bash
sw_vers
uname -m
sysctl -n machdep.cpu.brand_string
xcode-select -p || xcode-select --install
git --version
node --version
npx --version
~~~

Se Node.js estiver ausente, instale uma versão suportada/LTS do [Node.js](https://nodejs.org/). O Reflex instala dependências web próprias durante a inicialização: **não se deve executar `npm ci` na raiz do projeto** (não existe `package-lock.json` ali).

**3.2. Python 3.12 oficial por Terminal**

~~~bash
mkdir -p "$HOME/Downloads/vitta-one-install"
curl -fL --retry 3 -o "$HOME/Downloads/vitta-one-install/python312.pkg" \
  https://www.python.org/ftp/python/3.12.10/python-3.12.10-macos11.pkg
pkgutil --check-signature "$HOME/Downloads/vitta-one-install/python312.pkg"
sudo installer -pkg "$HOME/Downloads/vitta-one-install/python312.pkg" -target /
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 --version
~~~

O `sudo` solicita a senha do próprio macOS. Se o instalador já estiver presente e o Python 3.12 funcionar, pule a reinstalação.

**3.3. PostgreSQL 16 oficial via Postgres.app, pelo Terminal**

~~~bash
curl -fL --retry 3 -o "$HOME/Downloads/vitta-one-install/postgresql16.dmg" \
  https://github.com/PostgresApp/PostgresApp/releases/download/v2.9.6/Postgres-2.9.6-16.dmg

PG_MOUNT="$(mktemp -d /tmp/vitta-pg-mount.XXXXXX)"
hdiutil attach -nobrowse -quiet -mountpoint "$PG_MOUNT" \
  "$HOME/Downloads/vitta-one-install/postgresql16.dmg"

if [ -e /Applications/Postgres.app ]; then
  echo "Postgres.app existente preservado; confira se possui o PostgreSQL 16."
else
  sudo ditto "$PG_MOUNT/Postgres.app" /Applications/Postgres.app
fi
hdiutil detach "$PG_MOUNT"
rmdir "$PG_MOUNT"

/Applications/Postgres.app/Contents/Versions/16/bin/psql --version
~~~

Se já há `/Applications/Postgres.app`, não sobrescreva a versão existente às cegas. Confira também os [downloads do Postgres.app](https://postgresapp.com/downloads.html).

**3.4. Criar o PostgreSQL de QA ISOLADO (somente na primeira instalação)**

O banco do QA manual será `vitta_one_qa` e o de testes automatizados será `vitta_one_test`. O cluster ficará em `~/Library/Application Support/VittaOneQA/postgresql16` e usará apenas `127.0.0.1:55432`. **Não interfere nos bancos do PlakaLink ou de outros projetos.**

**Se já executou anteriormente o setup do Vitta-One e ele abriu no navegador, pule esta criação**. Reutilize sua configuração anterior; não crie outro cluster.

Na raiz do repositório:

~~~bash
cd ~/Documents/openspec
bash <<'BASH'
set -Eeuo pipefail
umask 077
PY="/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12"
PG="/Applications/Postgres.app/Contents/Versions/16/bin"
ROOT="$HOME/Library/Application Support/VittaOneQA"
DATA="$ROOT/postgresql16"
mkdir -p "$ROOT"
chmod 700 "$ROOT"

if [[ -e "$DATA" && ! -f .env.qa ]]; then
  echo "Cluster existente, mas .env.qa ausente. Recupere as credenciais; nada será alterado."
  exit 1
fi

if [[ ! -f .env.qa ]]; then
  PASS="$("$PY" -c 'import secrets; print(secrets.token_urlsafe(32))')"
  printf "export VITTA_QA_DB_PASSWORD='%s'\n" "$PASS" > .env.qa
  printf "export DATABASE_URL='postgresql+psycopg://vittaqa:%s@127.0.0.1:55432/vitta_one_qa'\n" "$PASS" >> .env.qa
  printf "export VITTA_ONE_SESSION_TTL_SECONDS='3600'\n" >> .env.qa
  printf "export VITTA_ONE_COOKIE_SECURE='false'\n" >> .env.qa
  printf "export VITTA_ONE_CLINIC_TIMEZONE='America/Sao_Paulo'\n" >> .env.qa
  printf "export VITTA_ONE_LOCAL_ADMIN_PREVIEW='true'\n" >> .env.qa
  printf "export REFLEX_TELEMETRY_ENABLED='false'\n" >> .env.qa
  chmod 600 .env.qa
fi

source .env.qa
EXPECTED="postgresql+psycopg://vittaqa:$VITTA_QA_DB_PASSWORD@127.0.0.1:55432/vitta_one_qa"
if [[ "$DATABASE_URL" != "$EXPECTED" ]]; then
  echo "URL do banco não corresponde ao ambiente QA dedicado."
  exit 1
fi
if [[ ! -e "$DATA/PG_VERSION" ]]; then
  PWFILE="$(mktemp "$ROOT/pw.XXXXXX")"
  trap 'rm -f "$PWFILE"' EXIT
  printf '%s\n' "$VITTA_QA_DB_PASSWORD" > "$PWFILE"
  "$PG/initdb" -D "$DATA" --username=vittaqa --encoding=UTF8 \
    --auth-host=scram-sha-256 --auth-local=scram-sha-256 --pwfile="$PWFILE"
  rm -f "$PWFILE"
  trap - EXIT
fi
if [[ "$(cat "$DATA/PG_VERSION")" != "16" ]]; then
  echo "A instância existente não é PG16; nada será sobrescrito."
  exit 1
fi

if ! "$PG/pg_ctl" -D "$DATA" status >/dev/null 2>&1; then
  "$PG/pg_ctl" -D "$DATA" -l "$ROOT/postgres.log" \
    -o "-c listen_addresses=127.0.0.1 -p 55432 -c unix_socket_directories=/tmp" start
fi

export PGHOST=127.0.0.1 PGPORT=55432 PGUSER=vittaqa PGPASSWORD="$VITTA_QA_DB_PASSWORD"
ACTUAL="$("$PG/psql" -d postgres -Atqc "SELECT current_setting('data_directory')")"
if [[ "$ACTUAL" != "$DATA" ]]; then
  echo "A porta está ligada a OUTRO PostgreSQL; operação interrompida."
  exit 1
fi
for DB in vitta_one_qa vitta_one_test; do
  FOUND="$("$PG/psql" -d postgres -Atqc "SELECT 1 FROM pg_database WHERE datname='$DB'")"
  if [[ "$FOUND" != "1" ]]; then "$PG/createdb" "$DB"; fi
done
echo "Cluster e bancos QA verificados."
BASH
~~~

O arquivo `.env.qa` armazena a senha gerada (modo `600`) e já é ignorado pelo Git (`.env.*`). **Não mostre, envie ou versione seu conteúdo**.

**3.5. Criar/ativar o ambiente Python**

~~~bash
cd ~/Documents/openspec
if [ ! -d .venv ]; then
  /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 -m venv .venv
fi
source .venv/bin/activate
python --version                  # deve ser 3.12.x
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
~~~

Não remova um `.venv` pré-existente sem primeiro verificar sua versão e preservar o que houver de importante.

### 4. Linux — Ubuntu 24.04

Exemplo para Ubuntu **24.04**, onde os pacotes usados abaixo estão disponíveis. Outras versões/distros requerem adaptação documentada pelo fornecedor.

~~~bash
sudo apt update
sudo apt install -y git python3.12 python3.12-venv python3-pip \
  nodejs npm postgresql-16 postgresql-client-16
sudo systemctl status postgresql --no-pager
python3.12 --version
psql --version
~~~

Crie a role/bancos locais (somente uma vez):

~~~bash
sudo -u postgres psql
~~~

No console `psql`:

~~~sql
CREATE ROLE vittaqa LOGIN;
\password vittaqa
CREATE DATABASE vitta_one_qa OWNER vittaqa;
CREATE DATABASE vitta_one_test OWNER vittaqa;
\q
~~~

A conexão padrão será `127.0.0.1:5432`, se não houver configuração diferente. **Se os bancos já existem, preserve-os**.

~~~bash
cd ~/Documents/openspec
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

umask 077
cat > .env.qa <<'ENV'
export DATABASE_URL='postgresql+psycopg://vittaqa:SENHA_CODIFICADA_PARA_URL@127.0.0.1:5432/vitta_one_qa'
export VITTA_ONE_SESSION_TTL_SECONDS='3600'
export VITTA_ONE_COOKIE_SECURE='false'
export VITTA_ONE_CLINIC_TIMEZONE='America/Sao_Paulo'
export VITTA_ONE_LOCAL_ADMIN_PREVIEW='true'
export REFLEX_TELEMETRY_ENABLED='false'
ENV
chmod 600 .env.qa
~~~

Substitua o placeholder de senha localmente. Senhas contendo caracteres como `@`, `:`, `/` ou `#` devem ser percent-encoded para a URL. Nunca salve isso no Git; a configuração só é carregada com `source .env.qa`.

### 5. Windows 11 — PowerShell

Instale os pacotes com o Gerenciador de Pacotes do Windows (se necessário, use instaladores oficiais):

~~~powershell
winget install --exact --id Git.Git
winget install --exact --id OpenJS.NodeJS.LTS
winget install --exact --id Python.Python.3.12
winget install --exact --id PostgreSQL.PostgreSQL.16
~~~

Durante a instalação do PostgreSQL, defina e guarde a senha local de `postgres`. Reinicie o PowerShell e verifique `py -3.12 --version`, `node --version`, `npx --version`.

~~~powershell
cd "$HOME\Documents"
git clone --branch develop https://github.com/vitta-one/openspec.git
cd openspec
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
~~~

Crie dois bancos locais *se não existirem*:

~~~powershell
$PgBin = "C:\Program Files\PostgreSQL\16\bin"
& "$PgBin\psql.exe" -h 127.0.0.1 -p 5432 -U postgres -d postgres
~~~

No `psql`:

~~~sql
CREATE DATABASE vitta_one_qa;
CREATE DATABASE vitta_one_test;
\q
~~~

Defina no **PowerShell atual**, usando a senha codificada para URL (nunca compartilhe o comando preenchido):

~~~powershell
$env:DATABASE_URL = 'postgresql+psycopg://postgres:SENHA_CODIFICADA_PARA_URL@127.0.0.1:5432/vitta_one_qa'
$env:VITTA_ONE_SESSION_TTL_SECONDS = '3600'
$env:VITTA_ONE_COOKIE_SECURE = 'false'
$env:VITTA_ONE_CLINIC_TIMEZONE = 'America/Sao_Paulo'
$env:VITTA_ONE_LOCAL_ADMIN_PREVIEW = 'true'
$env:REFLEX_TELEMETRY_ENABLED = 'false'
~~~

No Windows, execute comandos Python com `.\.venv\Scripts\python.exe` e comandos Reflex com `.\.venv\Scripts\reflex.exe`. As variáveis `$env:` são **temporárias** e precisam ser redefinidas ao abrir novo terminal.

### 6. Variáveis de ambiente necessárias

| Variável | Uso |
| --- | --- |
| `DATABASE_URL` | **Obrigatória**, PostgreSQL local; aceita `postgresql+psycopg://` |
| `VITTA_ONE_SESSION_TTL_SECONDS` | **Obrigatória**, inteiro positivo em segundos (ex.: `3600`) |
| `VITTA_ONE_COOKIE_SECURE` | `false` só em `localhost` HTTP; `true` em HTTPS |
| `VITTA_ONE_CLINIC_TIMEZONE` | `America/Sao_Paulo` |
| `VITTA_ONE_CLINIC_NAME` | Opcional; nome público real da clínica no portal |
| `VITTA_ONE_CLINIC_ADDRESS` | Opcional; endereço público real da clínica no portal |
| `VITTA_ONE_PUBLIC_URL` | URL pública sem segredo, usada no e-mail de ativação do paciente |
| `VITTA_ONE_LOCAL_ADMIN_PREVIEW` | `true` só para previews locais de leitura do Admin |
| `REFLEX_TELEMETRY_ENABLED` | `false` para desativar telemetria Reflex |
| `RESEND_API_KEY` | Opcional; integração real com Resend |
| `RESEND_FROM_EMAIL` | Opcional; remetente verificado no Resend |
| `VITTA_ONE_BOOTSTRAP_ADMIN_EMAIL` | Somente ao criar o primeiro Admin |
| `VITTA_ONE_BOOTSTRAP_ADMIN_PASSWORD` | Somente ao criar o primeiro Admin, nunca versionar |

Em macOS/Linux, após **cada novo terminal**, entre na pasta e execute:

~~~bash
cd ~/Documents/openspec
source .venv/bin/activate
source .env.qa
~~~

**Se você já usou `vitta-one-setup-terminal.sh` no Hackintosh**, mantenha as configurações existentes e descubra como o script de inicialização as carrega. Ele foi usado localmente, mas **não está versionado no repositório**. Não execute novamente o setup completo para apenas atualizar código.

### 7. Confirmar o banco ANTES de executar migrations

`reflex db migrate` altera o esquema do banco configurado; nunca execute sem validar o destino. Não imprima a senha da URL.

~~~bash
python - <<'PY'
import os
from sqlalchemy.engine import make_url
url = make_url(os.environ["DATABASE_URL"])
print("Host:", url.host, "Porta:", url.port, "Banco:", url.database)
assert url.host in ("127.0.0.1", "localhost"), "QA precisa ser local"
assert url.database == "vitta_one_qa", "Banco incorreto!"
PY
~~~

No Windows, adapte para executar com `.\.venv\Scripts\python.exe` ou confirme a conexão pelo `psql`. Verifique que a porta aponta para a instância correta (55432 no exemplo Mac; 5432 nos exemplos Linux/Windows).

Aplique as migrations **somente ao banco QA confirmado**:

~~~bash
reflex db migrate
python -m alembic current
python -m pip check
reflex compile --dry
~~~

A migration `f2a4c9d8e721` acrescenta campos de credencial temporária e status de e-mail do profissional. A migration `8c1d5e2f7a90` adiciona a role `PACIENTE`, o vínculo opcional e único do paciente, convites e histórico de reagendamento. Ambas são aditivas; migrações exigem backup, confirmação de destino e revisão antes de qualquer ambiente não descartável. O downgrade da nova capability é bloqueado quando existem contas, convites ou histórico que seriam perdidos. **Não faça downgrades automáticos.**

### 8. Criar o primeiro Administrador e fazer login

Execute o bootstrap **uma única vez** no banco QA, depois das migrations. No macOS/Linux:

~~~bash
export VITTA_ONE_BOOTSTRAP_ADMIN_EMAIL='qa-admin@example.invalid'
printf "Senha forte do novo Admin QA (não aparece): "
IFS= read -r -s VITTA_ONE_BOOTSTRAP_ADMIN_PASSWORD
echo
export VITTA_ONE_BOOTSTRAP_ADMIN_PASSWORD
python -m vitta_one.auth.bootstrap
unset VITTA_ONE_BOOTSTRAP_ADMIN_PASSWORD
~~~

No PowerShell, defina as variáveis equivalentes e execute `.\.venv\Scripts\python.exe -m vitta_one.auth.bootstrap`. O bootstrap não redefine a senha de Administrador existente. **Se seu Admin já foi criado, pule esta etapa.**

| Perfil | Login / rota |
| --- | --- |
| Administrador | `/login` → `/admin` |
| Recepcionista | `/recepcao` |
| Médico | `/medico` |
| Financeiro | `/financeiro` |

Uma instalação de QA anterior pode conter os usuários sintéticos `qa-recepcao@example.invalid`, `qa-medico-a@example.invalid`, `qa-medico-b@example.invalid` e `qa-financeiro@example.invalid`. **Eles não surgem automaticamente do `git clone`**: precisam ser criados por um procedimento de seed autorizado. Não há senha de teste padrão no repositório.

**Opcional — criar as quatro identidades fictícias para QA (macOS/Linux):** execute **somente** no banco `vitta_one_qa` local, após as migrations e com venv/variáveis carregadas. O código confirma o destino, não altera contas existentes e não cadastra pacientes. Isso permite testar login de Recepção/Financeiro e vincular as contas Médicas existentes pelo cadastro de profissional no Administrador.

~~~bash
printf "Senha única de QA para quatro contas (mínimo 12 caracteres): "
IFS= read -r -s VITTA_QA_USERS_PASSWORD
echo
export VITTA_QA_USERS_PASSWORD

python - <<'PY'
import os
import reflex as rx
from sqlalchemy.engine import make_url
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password
from vitta_one.auth.service import find_user_by_email
from vitta_one.models.auth import User

url = make_url(os.environ["DATABASE_URL"])
assert url.host in {"127.0.0.1", "localhost"} and url.database == "vitta_one_qa"
password = os.environ["VITTA_QA_USERS_PASSWORD"]
assert len(password) >= 12, "Senha QA precisa ter no mínimo 12 caracteres."
accounts = (
    ("qa-recepcao@example.invalid", Role.RECEPCIONISTA),
    ("qa-medico-a@example.invalid", Role.MEDICO),
    ("qa-medico-b@example.invalid", Role.MEDICO),
    ("qa-financeiro@example.invalid", Role.FINANCEIRO),
)
with rx.session() as db:
    for email, role in accounts:
        existing = find_user_by_email(db, email)
        if existing:
            assert existing.role == role.value, "Role divergente: " + email
            print("Identidade existente preservada:", email)
        else:
            db.add(User(email=email, role=role.value,
                        password_hash=hash_password(password)))
            print("Nova identidade fictícia:", email)
    db.commit()
PY
unset VITTA_QA_USERS_PASSWORD
~~~

As contas Médicas fictícias começam **sem profissional vinculado**; associe-as pela interface do Administrador informando o mesmo e-mail e uma especialidade válida. Em Windows, adapte a entrada segura de senha ao PowerShell e execute o mesmo Python com ` .\.venv\Scripts\python.exe ` (sem espaços dentro do comando). **Não execute esse seed em produção.**

Administradores podem usar **Novo profissional** (nome, e-mail, especialidades) para criar a conta Médica; o primeiro acesso precisa de troca de senha em `/primeiro-acesso`. Sem Resend, a criação local **não envia credenciais** ao médico.

### 9. Como iniciar, reiniciar e encerrar

No macOS, se o cluster QA estiver parado, inicie **somente** a instância dedicada:

~~~bash
PG="/Applications/Postgres.app/Contents/Versions/16/bin"
DATA="$HOME/Library/Application Support/VittaOneQA/postgresql16"
"$PG/pg_ctl" -D "$DATA" status || \
"$PG/pg_ctl" -D "$DATA" \
  -l "$HOME/Library/Application Support/VittaOneQA/postgres.log" \
  -o "-c listen_addresses=127.0.0.1 -p 55432 -c unix_socket_directories=/tmp" start
~~~

Execute o app na raiz com venv e ambiente carregados:

~~~bash
reflex run --env prod --single-port 2>&1 | tee reflex.log
~~~

Esse comando é compatível com a **versão Reflex fixada neste projeto**. No PowerShell, use `.\.venv\Scripts\reflex.exe run --env prod --single-port`. O modo de produção local não tem hot reload: para atualizar código, pare com `Ctrl+C` e inicie novamente.

Quando aparecer `App running at: http://0.0.0.0:3000/`, abra **<http://localhost:3000/login>**. `0.0.0.0` é o endereço de escuta, não o endereço recomendado no navegador.

Rotas importantes: `/admin`, `/admin/especialidades`, `/admin/profissionais`, `/recepcao`, `/medico`, `/medico/prescricao/[prescription_id]`, `/financeiro` e `/primeiro-acesso`. O Admin tem previews de leitura em `/admin/recepcao`, `/admin/agenda`, `/admin/atendimento`, `/admin/pacientes` e `/admin/financeiro` com o flag de QA habilitado.

**Parar a aplicação** com `Ctrl+C` não apaga os bancos. Para diagnóstico da porta 3000 no macOS, use `lsof -nP -iTCP:3000 -sTCP:LISTEN` antes de interromper qualquer processo. Não encerre processos de outros projetos.

### 10. Rodar testes e validar OpenSpec

Primeiro valide as specs:

~~~bash
npx -y @fission-ai/openspec@1.13.0 validate --all --strict --no-interactive
~~~

Para `pytest`, **nunca use o banco `vitta_one_qa` onde você testa o navegador**. Crie e migre `vitta_one_test` (passo 3/4/5). No macOS/Linux:

~~~bash
export QA_ORIGINAL_DATABASE_URL="$DATABASE_URL"
export DATABASE_URL="$(python - <<'PY'
import os
from sqlalchemy.engine import make_url
print(make_url(os.environ["DATABASE_URL"]).set(database="vitta_one_test").render_as_string(hide_password=False))
PY
)"

# Validar o destino separado de testes:
python - <<'PY'
import os
from sqlalchemy.engine import make_url
u = make_url(os.environ["DATABASE_URL"])
print("Banco exclusivo para testes:", u.host, u.port, u.database)
assert u.host in ("127.0.0.1", "localhost") and u.database == "vitta_one_test"
PY

reflex db migrate
python -m pytest -q
reflex compile --dry

export DATABASE_URL="$QA_ORIGINAL_DATABASE_URL"
unset QA_ORIGINAL_DATABASE_URL
~~~

Se ocorrer erro durante os testes, restaure `DATABASE_URL` antes de iniciar a aplicação. No PowerShell, use os executáveis do venv, troque temporariamente a URL para `vitta_one_test` e restaure depois. O CI executa esse fluxo em PostgreSQL 16 isolado.

Os testes de navegador Chromium usam `qa_browser/prescription_browser.py`, `scripts/qa_seed_prescriptions.py` e o workflow `.github/workflows/qa-prescriptions-browser.yml`. **O seed é para banco descartável**, exige `VITTA_ONE_QA_DISPOSABLE_DATABASE=yes` e **nunca deve ser executado no banco QA persistente**, mesmo com dados sintéticos. Consulte o workflow antes de reproduzi-lo.

### 11. Resend (opcional) e segurança do primeiro acesso

No servidor, defina `RESEND_API_KEY` e `RESEND_FROM_EMAIL` (remetente verificado no Resend). Nunca registre chaves em código, Git, prints ou mensagens. Sem essas variáveis, o cadastro local do Médico acontece, mas o e-mail fica com status **NOT_CONFIGURED**. O status **ACCEPTED** quer dizer somente que a API aceitou a requisição; não confirma entrega/abertura. Erros e timeouts não disparam reenvio automático.

A senha temporária é gerada criptograficamente, salva somente em hash e expira em **24 horas**; o Médico precisa escolher uma nova senha em `/primeiro-acesso` antes de acessar funcionalidades clínicas. A transmissão de senha por e-mail é menos segura que um convite com token único e deve ser revisada antes de produção real.

O convite do portal do paciente usa as mesmas credenciais do Resend e exige também `VITTA_ONE_PUBLIC_URL`. A Recepção precisa confirmar consentimento em uma ação separada; o cadastro não cria uma conta. O código é enviado por e-mail, persistido somente como hash, expira em 24 horas e é consumido uma vez. Se o envio não for aceito, nenhum acesso é ativado; a equipe pode emitir outro convite após confirmar consentimento novamente. `VITTA_ONE_CLINIC_NAME` e `VITTA_ONE_CLINIC_ADDRESS` devem conter os dados reais da unidade; quando qualquer um estiver ausente, o portal informa que o endereço ainda precisa ser configurado.

Cloudinary (exames), ZapSign (assinatura de prescrições) e Asaas (pagamentos) **não precisam de configuração para testar o MVP atual**. Sua integração continua planejada em `docs/roadmap/next-capabilities-2026-10-14.md`.

### 12. Atualizar depois de novos merges — sem reinstalar tudo

1. Pare o servidor Reflex com `Ctrl+C`, mas **preserve o PostgreSQL**.
2. Verifique `git status --short` e preserve alterações locais.
3. Execute `git fetch origin`, `git switch develop` e `git pull --ff-only`.
4. Ative `.venv` e carregue suas variáveis de ambiente **existentes**.
5. Execute `python -m pip install -r requirements-dev.txt`.
6. Confirme host/porta/banco QA; execute `reflex db migrate` se houver novas migrations.
7. Faça `reflex compile --dry` e reinicie com `reflex run --env prod --single-port 2>&1 | tee reflex.log`.
8. Confira o login antigo; **não execute novamente o bootstrap ou seed do CI**.

Se seu Hackintosh já tem o iniciador `~/Downloads/vitta-one-iniciar-terminal.sh`, pode continuar usando-o após os passos acima. Ele não está versionado no Git. Para ver de onde ele carrega as variáveis sem despejar senhas, inspecione os nomes das instruções com `grep -nE 'source|env.qa|DATABASE_URL|reflex run' ~/Downloads/vitta-one-iniciar-terminal.sh`.

### 13. Erros comuns

| Problema | O que verificar |
| --- | --- |
| `npm ci` mostra `EUSAGE` | **Não usar na raiz**: sem `package-lock.json`. Dependências estão em `requirements-dev.txt` e `.web/` é gerenciado pelo Reflex. |
| `python3.12: command not found` | No Mac, use o caminho absoluto do Python 3.12 mostrado acima. |
| `brew: command not found` | Homebrew **não é necessário** para este guia de Hackintosh. |
| `docker: command not found` | Docker **não é necessário**. |
| `DATABASE_URL deve ser definida` | Carregue `source .env.qa` no mesmo terminal em que iniciará o Reflex. |
| `VITTA_ONE_SESSION_TTL_SECONDS` ausente | Defina inteiro positivo como `3600`. |
| `connection refused` no PostgreSQL | Confira serviço, porta e cluster; **não apague nem reinicialize dados**. |
| `password authentication failed` | Confira usuário/senha da instância correta, sem revelar segredos. |
| `UndefinedColumn` / `column ... does not exist` | Código mais recente que o schema: confira banco correto e aplique migrations. |
| Login não persiste por HTTP local | Confira `VITTA_ONE_COOKIE_SECURE=false` no **localhost apenas**. |
| Porta 3000 ocupada | Identifique primeiro o processo com `lsof`; não mate processos sem verificar. |
| `DeprecationWarning` do Reflex | Avisos da 0.9.x não exigem atualizar a versão fora de change. |
| `async generator ignored GeneratorExit` após `Ctrl+C` | Pode estar associado ao encerramento; consulte `reflex.log` se ocorrer durante uso normal. |
| Médico não recebeu e-mail | Confira status do Resend; `NOT_CONFIGURED` significa sem envio. |
| `git pull` não atualiza a aplicação | Além de Git, atualize dependências, migrations e reinicie processo. |

Logs locais: `tail -n 100 reflex.log`, `python -m pip check`, `git status --short`. Não compartilhe conteúdo clínico, tokens ou senhas.

### 14. Checklist final de instalação

- [ ] Python 3.12, Node/npx, Git e PostgreSQL 16 funcionando.
- [ ] Repositório na branch correta e `.venv` com as dependências instaladas.
- [ ] Banco `vitta_one_qa` identificado e conexão testada, sem interferir em outros projetos.
- [ ] Variáveis de ambiente carregadas e arquivo local ignorado pelo Git.
- [ ] Migrations aplicadas ao **banco correto**.
- [ ] Primeiro Administrador criado (uma vez) e senha guardada com segurança.
- [ ] `reflex compile --dry` aprovado.
- [ ] Aplicação acessível em `http://localhost:3000/login`.
- [ ] Testes executados separadamente em `vitta_one_test` e OpenSpec validado.
- [ ] Cadastro/agenda testados com **dados sintéticos** e envio real de e-mail somente se explicitamente configurado.

## Demonstração local completa sem Resend (apenas QA isolado)

O fluxo a seguir só é habilitado quando **todos** os critérios são verdadeiros:
`VITTA_ONE_LOCAL_ADMIN_PREVIEW=true`, `DATABASE_URL` apontando para PostgreSQL
local (`127.0.0.1` / `localhost`) no banco **`vitta_one_qa`**, porta
`5432`, `5433` ou `55432`, e `VITTA_ONE_PUBLIC_URL=http://localhost:3000`
(ou `http://127.0.0.1:3000`). Fora deste ambiente, as ações locais somem
e o servidor também as recusa. Não habilite isso no servidor de demonstração público.

1. Acesse o login como Administrador e abra **Administração** (`/admin`).
2. Cadastre uma especialidade e clique em **Novo profissional**. Informe nome, e-mail,
   especialidade e, no QA local, uma **senha do Médico com 12+ caracteres**.
   A credencial é armazenada como hash Argon2id; não depende de Resend.
3. Na mesma página, em **Acesso da Recepção · QA local**, informe um e-mail distinto
   e outra senha com 12+ caracteres. Clique em **Criar login de recepcionista**.
4. Saia da conta Admin. Entre com o e-mail/senha da Recepção; abra
   `/recepcao/pacientes` e cadastre o paciente com CPF válido, nome e telefone.
5. Com o paciente selecionado, em **Acesso ao portal**, preencha o bloco
   **Habilitar login do paciente (QA)**, confirmando o consentimento e definindo
   e-mail e senha próprios para esse paciente.
6. Saia da Recepção. Entre como Paciente, abra `/paciente/agendar`, selecione
   especialidade, médico, data/hora e confirme a consulta.
7. Entre como Médico usando a credencial criada no passo 2 e confira
   `/medico/agenda`. Entre novamente na Recepção para confirmar a chegada,
   e depois realize o atendimento médico com histórico e prescrição.

As senhas de teste **não são devolvidas ao navegador depois de salvar**, nem
ficam em Reflex State. Anote-as em seu gerenciador local. O usuário Médico e
Recepcionista só existem após cadastro autenticado pelo Admin; a Recepção só
pode ativar o paciente **já cadastrado e selecionado**, com consentimento.
As rotas e serviços possuem autorização server-side. Não use dados reais.

Em ambientes não locais, o Médico mantém o onboarding por Resend, enquanto o
Paciente recebe convite e ativa um código único em `/ativar-paciente`.
A criação de Recepcionista em produção precisa de fluxo de convite e gestão de
colaboradores próprios — a operação de QA não substitui essa funcionalidade.

## Cadastro médico simplificado (QA / Resend)

O fluxo de **Novo profissional** aceita nome, e-mail e uma ou mais especialidades. Se o e-mail ainda não possuir conta local, o servidor cria a identidade `MEDICO` com senha aleatória temporária (somente hash Argon2id em persistência), obrigando troca em `/primeiro-acesso` dentro de 24 horas.

Para ativar o envio real **somente em ambiente autorizado**:

```bash
export RESEND_API_KEY='<chave-real-somente-no-ambiente-do-servidor>'
export RESEND_FROM_EMAIL='Vitta-One <acesso@dominio-verificado.example>'
```

Os valores acima são placeholders, **não credenciais funcionais**. O remetente precisa existir e ser validado no Resend. Nunca versionar chaves. O código utiliza a API REST via httpx no servidor, com timeout explícito e chave de idempotência por operação. Um status `ACCEPTED` confirma apenas aceitação do pedido HTTP pelo provedor, **não entrega ou leitura** do e-mail. Sem configuração, o usuário é criado com `NOT_CONFIGURED`, sem qualquer envio e sem falso aviso de sucesso. Em timeout incerto, não há reenvio automático da mesma senha.

**Segurança:** envio de senha temporária por e-mail possui riscos e não substitui um onboarding baseado em token único. Antes de liberar isso para dados reais, aprovar política de recuperação, retenção, remetente/domínio e monitoramento. A migration `f2a4c9d8e721` é aditiva, mas deve ser testada em banco isolado antes de aplicar a qualquer ambiente com dados.

## Rotas protegidas

- `/login`: autenticação local, sem cadastro público;
- `/admin`: painel com três especialidades e três profissionais recentes e horários de atendimento agrupados por dia;
- `/admin/especialidades` e `/admin/profissionais`: diretórios completos com busca, filtros e paginação, exclusivos do Administrador;
- `/primeiro-acesso`: troca obrigatória de senha temporária Médica;
- `/medico/agenda` e `/medico/pacientes`: agenda e lista derivadas do profissional associado à sessão;
- `/paciente`: calendário, histórico e consultas vinculadas à conta do paciente;
- `/paciente/agendar`: o paciente autenticado escolhe especialidade, médico e horário disponível, revisa e confirma a própria consulta;
- `/ativar-paciente`: ativação por e-mail, código de uso único e senha escolhida pelo paciente;
- `/recepcao`: agenda de Consultas, confirmação de chegada, cadastro/localização de pacientes, entrada avulsa, reavaliação, retirada e acompanhamento da fila ativa;
- `/medico`: fila elegível, registro clínico, múltiplas Prescrições com itens e histórico concluído do paciente;
- `/medico/prescricao/[prescription_id]`: visualização protegida e pronta para impressão da Prescrição do Médico autor, sem assinatura digital nesta etapa;
- `/financeiro`: shell protegido do Financeiro;
- `/acesso-negado`: estado autenticado para tentativa de acesso a uma role incompatível.

Financeiro ainda permanece shell. Administrador executa a gestão do diretório e Recepção/Médico executam a capability de fila; prioridade é sempre informada pela operação (`VERMELHO`, `AMARELO`, `VERDE`) e nunca é calculada ou elevada automaticamente pelo Vitta-One. A autorização é revalidada no backend e não depende apenas de componentes escondidos no frontend.

Uma Consulta agendada continua fora da fila até a Recepção usar **Confirmar chegada**. Quando o Médico marcado chama o paciente, nasce um único `ClinicalCareRecord`. Durante `EM_ANDAMENTO`, o Médico pode salvar o registro clínico e criar uma ou mais Prescrições com itens. Ao finalizar, Consulta/fila passam para `CONCLUIDA`/`FINALIZADO`; Atendimento e Prescrições tornam-se somente leitura e passam a integrar o histórico. A Prescrição possui visualização HTML/CSS para impressão, mas **a assinatura ZapSign ainda não está implementada**. Atendimentos avulsos de pronto-socorro não criam uma Consulta agendada: o registro clínico e as prescrições são vinculados diretamente à passagem da fila, com histórico preservado após finalização. O fluxo de autogendamento não altera a classificação da fila.

## Fluxo de desenvolvimento

Mudanças relevantes devem seguir o ciclo:

```text
Contexto → Explore → Propose → Review → Apply → Archive
```

Antes de alterar funcionalidades, leia `AGENTS.md`, `docs/project-overview.md`, `docs/domain-model.md` e `openspec/config.yaml`.


### Jornada de autogendamento e homologação

O cadastro operacional da recepção em `/recepcao/pacientes` permite enviar convite de acesso mediante consentimento. O paciente ativa a conta em `/ativar-paciente` usando e-mail, código temporário e senha de pelo menos 12 caracteres. O agendamento em `/paciente/agendar` usa **a identidade da sessão**, não um ID de paciente recebido do navegador. A seleção é feita por especialidade ativa, médico ativo e horários livres para os próximos 45 dias. A reserva usa o mesmo serviço transacional da recepção, impede sobreposição no mesmo horário e aparece nas agendas de paciente, médico e recepcionista.

**Caminho sintético de demonstração:** recepcionista cadastra paciente, confirma consentimento e envia convite; paciente ativa e entra; escolhe especialidade, médico, data/hora e confirma; entra como médico para verificar a agenda; recepção confirma chegada para inserir o agendamento na fila; médico chama e finaliza. A confirmação real de entrega dos e-mails via Resend depende de credenciais e remetente verificado configurados na implantação, e não é verificada pelo CI. O Chromium usa ativação/usuários sintéticos no banco descartável. Não execute o seed de QA em produção.

O ambiente de desenvolvimento não deve mostrar prescrições ou dados pessoais reais nas capturas. Para homologação de migração e e-mail no ambiente final: faça backup PostgreSQL, valide `alembic upgrade head` no destino controlado, confirme recebimento efetivo no endereço de testes, ativação única e login, e só então habilite a demonstração pública.
