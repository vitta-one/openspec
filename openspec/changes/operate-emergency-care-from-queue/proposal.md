# Change: operar pronto-socorro exclusivamente pela fila

## Problema
A interface atual anuncia Agenda, consultas programadas, horários e reagendamentos, enquanto o produto definido pelo responsável é **pronto-socorro exclusivamente presencial, sem agendamento**. Além disso, o fluxo já suporta entrada avulsa na fila, mas `ClinicalCareRecord` e `Prescription` exigem uma `Consultation` agendada. Isso impede prontuário e prescrição no atendimento real.

## Objetivo
Operar Recepção → cadastro/localização → entrada na fila → priorização informada → chamada pelo Médico → atendimento clínico/prescrição → finalização, mantendo autenticação por papel, integridade e histórico.

## Escopo
- Priorizar fila na home e navegação da Recepção; retirar calendários/agendas do produto ativo.
- Médico atende pacientes chamados da fila, com prontuário e prescrições ligados à passagem real pelo pronto-socorro.
- Histórico clínico/paciente mostra apenas atendimentos autorizados e persistidos.
- Auditoria, controle de concorrência, RBAC e proteção de conteúdo clínico.
- Testes de fluxo real no PostgreSQL descartável e screenshots Chromium de telas por perfil.

## Fora do escopo
- Criação de horários/slots, reserva de consultas, reagendamento, check-in de agendamentos.
- Chamada médica pela recepção ou classificação automática de prioridade.
- Exames/financeiro futuros; integrações externas não implementadas.

## Compatibilidade e segurança
Não remover tabelas/consultas históricas nesta change sem desenho de migração e aceite explícito. Despublicar as rotas não significa excluir os dados legados. Não criar Consulta fictícia para dar suporte ao pronto-socorro; o vínculo clínico será direto à entrada da fila.

## Entrega incremental
A primeira etapa altera a navegação e o dashboard operacional sem apagar dados; o suporte clínico de walk-in exige uma migração aditiva própria, com revisão e QA PostgreSQL. Esta change só deve ser declarada concluída quando o fluxo ponta a ponta estiver validado.
