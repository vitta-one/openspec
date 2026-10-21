# Expediente semanal do médico

O Administrador configura em **Administração → Horários de atendimento**: médico,
dia inicial e final (segunda a domingo), início e fim do expediente e duração
das consultas (30 ou 60 minutos). O sistema grava **uma escala semanal por médico**
e publica slots livres na janela móvel de **45 dias**, no timezone configurado
por `VITTA_ONE_CLINIC_TIMEZONE`.

O paciente seleciona especialidade, médico e um slot disponível. Ao abrir a
agenda do médico, os slots das próximas 45 dias são gerados automaticamente,
sem alterar reservas existentes ou os slots individuais criados manualmente.

**Editar escala** desativa apenas slots futuros que foram gerados pela escala
anterior e ainda estejam livres. Não cancela consultas já marcadas e não
reativa slots explicitamente desativados. Uma consulta já reservada permanece no
histórico mesmo se a escala mudar; ao cancelar ou reagendar uma consulta antiga,
o horário fora da nova escala não volta a ficar livre.

Use horários como 08:00–17:00 com blocos de 30 minutos (08:00, 08:30…16:30).
A faixa deve caber em blocos completos, sem virar a meia-noite e com dias
em ordem crescente. Para plantões que cruzam a semana ou intervalo de almoço,
ainda é necessário cadastrar slots explícitos conforme o procedimento anterior.

Na primeira execução após atualizar `develop`, rode **`reflex db migrate`**
com backup do banco e `.env.qa` carregado. Não execute seed do CI no banco de QA.
