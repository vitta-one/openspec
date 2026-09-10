<!-- reflex managed begin (do not edit inside this block; add custom content outside the markers) -->
# Agents

This project uses the **Reflex agent skills** — up-to-date knowledge for building full-stack Python web apps with [Reflex](https://reflex.dev). Install them first, then use them as described below.

## Installing the Skills

Before working on this project, make sure the Reflex skills are available to you.

### Claude Code

If the skills are not already available, install them yourself by running these shell commands:

```bash
claude plugin marketplace add reflex-dev/agent-skills
claude plugin install reflex@reflex-agent-skills
```

Newly installed plugins load on the next session. After installing, tell the user to restart the session so the skills auto-load; until then, read the skill files directly from `~/.claude/plugins/` when you need them.

### Other agents (Cursor, OpenCode, Codex, Pi)

```
npx skills add reflex-dev/agent-skills
```

Or clone https://github.com/reflex-dev/agent-skills and copy the `skills/` folders into your agent's skill directory (see the repo README for paths).

### Verifying

Before writing or editing any Reflex code, confirm these three skills are available: `reflex-docs`, `setup-python-env`, and `reflex-process-management`. If they are not, STOP and run the install step above — do not proceed without them.

## Using the Skills

### Reflex documentation

For anything about Reflex APIs — components, state management, events, styling, database, routing, authentication — use the **reflex-docs** skill rather than relying on memory. It carries current, version-accurate docs.

### Initializing a new Reflex project

When starting a new Reflex project or setting up a development environment, you **must** follow the **setup-python-env** skill before doing anything else.

Do not skip any steps. Do not assume a virtual environment or Reflex is already available — always verify first by following the skill's instructions in order.

After the environment is ready and Reflex is installed, run:

```bash
reflex init
```

Then proceed with the user's request.

### Managing a Reflex process

When you need to compile, run, reload, or debug a Reflex application, follow the **reflex-process-management** skill for the correct sequence and error investigation steps.
<!-- reflex managed end -->

# Vitta-One — Project Instructions

## Contexto obrigatório

Antes de alterações relevantes, leia:

- `docs/project-overview.md`;
- `docs/domain-model.md`;
- `openspec/config.yaml`;
- a change ativa em `openspec/changes/`, quando existir.

Não use contexto implícito para preencher decisões marcadas como abertas.

## Arquitetura

- Reflex é o framework full-stack obrigatório da aplicação web.
- O pacote da aplicação é `vitta_one/`.
- O diretório `openspec/` é reservado exclusivamente ao OpenSpec e não deve ser usado como pacote Python.
- PostgreSQL é o banco de dados definido para o projeto.
- Preferir componentes, State, eventos, páginas, rotas, mecanismos de backend e recursos nativos do Reflex.
- Não introduzir React, Next.js, Vue, Angular, Streamlit, Express, FastAPI ou framework equivalente sem uma mudança arquitetural explicitamente aprovada.
- Evitar dependências novas quando a plataforma ou a biblioteca padrão atenderem ao requisito.

## OpenSpec

- Mudanças funcionais ou técnicas relevantes devem utilizar OpenSpec.
- Seguir o ciclo `Explore → Propose → Review → Apply → Archive`.
- Não iniciar implementação de uma funcionalidade relevante antes de revisar proposal, specs, design e tasks aplicáveis.
- `openspec/specs/` representa comportamento consolidado; não preencher specs finais antecipadamente fora do fluxo de changes.
- Manter changes delimitadas, incrementais e verificáveis.

## Segurança e dados

- Autorização deve ser aplicada no lado servidor; ocultar componentes na UI não é controle de acesso.
- Validar entradas no lado servidor, mesmo quando houver validação de interface.
- Não hardcodar ou versionar credenciais, tokens, chaves ou segredos.
- Tratar dados pessoais, financeiros e clínicos como sensíveis.
- Evitar registrar dados clínicos ou pessoais desnecessários em logs e mensagens de erro.
- Integrações com Cloudinary, ZapSign e Asaas devem usar configuração por ambiente e, quando implementadas, tratar autenticação, timeouts, rate limits, retries seguros e falhas externas.
- ZapSign e Asaas devem permanecer em sandbox enquanto o projeto acadêmico assim exigir.

## Qualidade

- Fazer apenas alterações necessárias ao escopo da change atual.
- Reutilizar código existente quando apropriado e evitar duplicação.
- Preservar convenções existentes e seguir os idioms do Reflex.
- Para funcionalidades, testar caminho feliz, validações, estados vazios, duplicidades relevantes, erros e falhas externas quando aplicável.
- Interfaces devem ser responsivas, acessíveis por teclado, possuir foco visível, contraste adequado e estados de loading, erro, vazio e sucesso quando pertinentes.
- Respeitar `prefers-reduced-motion` quando houver animações não essenciais.
- Antes de considerar uma alteração Reflex concluída, executar pelo menos `reflex compile --dry` e os testes relevantes disponíveis.

## Operações de risco

- Antes de exclusões, migrações destrutivas, sobrescritas ou mudanças de produção, fazer inspeção somente leitura e preferir alternativas reversíveis, backup ou dry-run.
- Não executar comandos destrutivos com dados reais sem escopo explicitamente confirmado.

## Documentação e Git

- Escrever documentação do projeto e artefatos OpenSpec em português brasileiro.
- Não versionar `.venv/`, `.env`, segredos, logs locais ou caches gerados.
- Não editar o bloco gerenciado pelo Reflex no topo deste arquivo; adicionar regras específicas do Vitta-One fora dos marcadores.
