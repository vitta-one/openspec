## Why

A ficha da Recepção exibe apenas identidade parcial e atalhos. A equipe precisa consultar consultas futuras, situação ativa na fila e histórico operacional sem navegar por módulos ou acessar dados clínicos restritos.

## What Changes

- Projetar identificação persistida com CPF mascarado, nome, telefone opcional e status real do acesso ao portal.
- Exibir próximas consultas e histórico paginado de consultas, com profissionais e situações, além de entrada ativa e movimentações recentes na fila.
- Substituir a navegação para uma nova página por um modal compartilhado de agendamento, com paciente da ficha bloqueado e atualização das consultas após confirmação.
- Abrir o mesmo modal pelo dashboard e Agenda sem duplicar os serviços de reserva existentes; preservar a rota de agendamento existente por compatibilidade.
- Impedir entradas ativas duplicadas no fluxo avulso da fila, com serialização transacional no PostgreSQL.
- Manter o cadastro e o gerenciamento de portal sob as permissões atuais, sem alterar senhas, tokens, prontuário ou modelos físicos.

## Capabilities

- MODIFIED: patient-reception-queue.
- MODIFIED: appointment-scheduling.

## Fora de escopo

Alterar CPF, permitir acesso a diagnósticos/anamnese/prescrições na Recepção, inventar novas operações de autenticação, criar endpoint REST, remover a rota legada de agendamento e alterar estados clínicos.
