# Resend no Vitta One — configuração de e-mail (QA local)

O Vitta One já utiliza o adaptador server-side `vitta_one/professional_directory/email_sender.py` para enviar **credenciais temporárias de Médicos** e **convites de ativação do portal do Paciente**. Esta configuração habilita o serviço existente, sem implantar outra integração.

## 1. Chave e remetente

1. Cadastre uma conta em https://resend.com e gere uma API key restrita ao envio.
2. Configure e verifique um domínio/remetente da clínica no painel do Resend. Não use o e-mail pessoal do funcionário como remetente.
3. No desenvolvimento, edite `.env.docker` **somente na sua máquina** (`chmod 600 .env.docker`). Mantenha as demais linhas e acrescente:

```dotenv
# Nunca versionar este arquivo. Copiar somente para o ambiente local.
RESEND_API_KEY=re_SUBSTITUIR_PELA_CHAVE_REAL
RESEND_FROM_EMAIL="Vitta One <acesso@seudominio.com.br>"
VITTA_ONE_PUBLIC_URL=http://localhost:3000
```

**Atenção:** `VITTA_ONE_PUBLIC_URL` deve refletir a URL pela qual o destinatário consegue acessar o portal; `localhost` só funciona no próprio computador. Um convite externo exige URL pública HTTPS e domínio autorizado — ainda não configure produção aqui.

## 2. Carregar as variáveis e iniciar

`make dev` importa `.env.docker` por meio de `scripts/dev-local.sh`, e o Reflex herda `RESEND_API_KEY` e `RESEND_FROM_EMAIL`. Reinicie o `make dev` depois de editar o arquivo.

A API de envio é `https://api.resend.com/emails`, chamada exclusivamente pelo servidor usando `httpx`. Nenhuma chave deve aparecer no browser, Git, URL, captura de tela ou logs.

## 3. Testar o fluxo

- Médico: em **Administração → Funcionários → Novo funcionário → Médico**, informe os dados e especialidades. Em ambiente normal de convite (sem senha QA digitada), uma credencial temporária expira em 24 horas; primeiro login exige troca.
- Paciente: na **Recepção → Pacientes → Ficha → Editar dados e acesso**, confirme consentimento e envie convite. O link de ativação contém um código de uso único.
- Em QA com senha escolhida manualmente para Médico, o envio de senha temporária não ocorre; esse caso é esperado.

O resultado **ACCEPTED** significa apenas que o Resend aceitou a requisição HTTP; não prova entrega na caixa de entrada. **FAILED**, **UNKNOWN** e **NOT_CONFIGURED** não devem ser exibidos como enviados.

## 4. Segurança e limites

Nunca inclua a API key em commits, issues, prints ou mensagens. A operação atual usa timeout e identificador único; em resultado incerto não reenvie automaticamente, pois o servidor pode já ter aceitado o e-mail. Consulte o status no provedor e execute uma reemissão apenas pelo fluxo administrativo explícito. Mensagens contêm informação de acesso e, por isso, não devem ser armazenadas como logs de aplicação.

Para validação sem enviar e-mails reais, use os testes automatizados em `tests/test_medical_email_onboarding.py`.
