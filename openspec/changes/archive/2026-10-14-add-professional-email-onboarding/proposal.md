## Why

A administração exige nome, identificador profissional manual e vínculo com uma conta de Médico criada externamente. Usuários leigos deveriam cadastrar um profissional somente com nome, e-mail e especialidades. Um onboarding seguro deve gerar credenciais aleatórias e comunicar o resultado real do provedor de e-mails.

## What Changes

- Cadastro de novo profissional com nome/e-mail/especialidades.
- Identificador interno único gerado no servidor sem semântica de conselho profissional.
- Operação atômica cria `User(MEDICO)`, profissional e associações, ou reutiliza conta Médica elegível.
- Primeira senha temporária gerada criptograficamente, persistida somente como hash; expira após 24h e exige troca.
- Envio pelo Resend somente no servidor, com configuração de ambiente, idempotência e status técnico (aceito/falha/indeterminado/sem configuração).
- Preservação de contas e cadastros legados; nenhum e-mail real nos testes.

## Modified Capabilities
- `professional-specialty-management`.
- `access-control`.

## Non-goals
- Cadastro público.
- Importação de CRMs, verificação de conselhos, assinatura digital, recuperação pública de senha.
- Garantia de entrega na caixa de entrada (o provedor apenas confirma aceitação da requisição).
- Migração destrutiva, alteração de credenciais existentes ou ambiente de produção.

## Risks
Senha enviada por e-mail é menos segura que convite com token de uso único. Iniciar com senha expirada em 24h e troca obrigatória; documentar evolução para convite-token antes de produção real. Não autorizar operações clínicas enquanto senha temporária estiver ativa. Falha de provedor não deve deixar registros sem status honesto.

## Impact
Models, migration, auth, domain/application state, interface Admin e testes. Resend opcional configurado apenas via env. Atualizar `docs/roadmap` conforme execução.
