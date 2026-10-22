## Why

A Recepção precisa abrir o dia de trabalho e entender rapidamente quem chega, em que horário, com qual profissional e em que situação está a consulta. O painel atual começa por indicadores e um calendário semanal; a referência anexada organiza a operação em uma tabela diária mais fácil de percorrer.

## What Changes

- Substituir a página inicial por uma tabela do dia atual no fuso da clínica, seguindo a hierarquia e o espaçamento da imagem fornecida.
- Incluir nome e telefone do paciente, profissional, especialidades cadastradas, status e acesso à Agenda.
- Adicionar busca rápida global de pacientes no topo e busca na tabela por nome, telefone ou CPF, além de filtro por profissional e paginação de sete linhas aplicada no servidor.
- Guardar telefone opcional no cadastro de pacientes, com validação, normalização e migration compatível com registros existentes.
- Preservar a tipografia, os tokens e as rotas já existentes, sem inserir unidade, prontuário ou registros fictícios.
- Manter Agenda, Pacientes e Fila como módulos protegidos independentes.

## Capabilities

- MODIFIED: reception-operational-dashboard.
- MODIFIED: patient-reception-queue.

## Fora de escopo

Unidade ou número de prontuário sem modelo persistido, seleção de especialidade por consulta, ações clínicas na tabela, alterações de RBAC, consulta em tempo real, dados de demonstração e reescrita do shell global.
