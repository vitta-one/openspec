# Homologação no banco local (sem Resend)

Este procedimento **não substitui o teste de convite por e-mail**: testa os logins
e o agendamento com registros sintéticos e um banco isolado.

1. Inicie a aplicação local com `source .venv/bin/activate`, `source .env.qa`
   e `reflex run --env prod --single-port`. O PostgreSQL deste procedimento é
   exclusivamente `vittaqa@127.0.0.1:5433/vitta_one_qa`.
2. Admin em `/admin`: crie uma especialidade e, em **Novo profissional**, um
   Médico usando `qa-medico@example.invalid`. Configure horários disponíveis.
3. Admin em **Acessos da Recepção**: crie `qa-recepcao@example.invalid` com
   senha de pelo menos 12 caracteres.
4. Saia da sessão e entre como Recepcionista. Em `/recepcao/pacientes`,
   cadastre paciente com nome, telefone e **CPF válido fictício**.
5. Para testar localmente sem e-mail, em outro terminal com ambiente carregado:
   ```bash
   python -m scripts.qa_local_logins --role medico --email qa-medico@example.invalid
   python -m scripts.qa_local_logins --role paciente --email qa-paciente@example.invalid --cpf CPF_FICTICIO_CADASTRADO
   ```
   As senhas são solicitadas sem eco. O utilitário só opera com a combinação
   exata de banco/porta/usuário local e flag explícito de preview QA, não
   substitui conta já ativada nem cria pacientes/profissionais.
6. Entre como Paciente, vá a `/paciente/agendar`, escolha especialidade,
   médico, horário e confirme.
7. Entre como Médico em `/medico/agenda` e confira a consulta.
   Entre como Recepcionista e confirme chegada. Então retorne como Médico
   para chamar e atender.

Sem Resend, **não está validado** o envio de convite e a ativação por código.
Para verificar essa etapa, configure `RESEND_API_KEY`,
`RESEND_FROM_EMAIL` e `VITTA_ONE_PUBLIC_URL` em um ambiente autorizado.
Use apenas e-mails de testes controlados e nunca use dados clínicos reais.
