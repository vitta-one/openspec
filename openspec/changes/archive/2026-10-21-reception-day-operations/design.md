# Design: operação diária da Recepção

## Direção

A tela principal assume o padrão da referência anexada: título e data primeiro, controles de busca e profissional logo abaixo e uma tabela única com paginação no rodapé. O shell e a tipografia existentes do Vitta-One permanecem intactos. Os novos espaçamentos ficam locais à tela e usam tokens de superfície, texto, borda e foco já definidos.

## Hierarquia e tarefas

1. Identificar a operação do dia e a data local da clínica.
2. Localizar um cadastro no topo por nome, telefone ou CPF e, na tabela, uma consulta do dia pelos mesmos campos.
3. Restringir a lista a um profissional.
4. Ler horário, paciente, contato, profissional, especialidades e situação.
5. Abrir a Agenda existente para agir sobre uma consulta.
6. Percorrer páginas sem carregar a lista inteira no navegador.

## Dados e limites

- A busca rápida do topo retorna no máximo oito identidades mínimas, exige role Recepcionista e encaminha a pessoa selecionada para Pacientes.

- A data local vem de clinic_today_iso e seu intervalo é convertido para UTC antes da consulta.
- O backend conta e pagina no SQL. A página padrão tem sete linhas e inclui cancelamentos.
- Telefone é opcional, fica no modelo Patient, é armazenado apenas como dígitos e pode estar ausente em dados legados.
- A consulta tem profissional, mas não guarda uma especialidade específica. A tabela mostra todas as especialidades ativas associadas ao profissional; não afirma que uma delas foi selecionada para a consulta.
- CPF participa da busca, mas não é serializado para a tela.
- A projeção não consulta conteúdo de fila ou de prontuário.
- As ações da linha continuam limitadas à navegação para o módulo Agenda.

## Responsividade e acessibilidade

- Busca, filtro e ações fluem em coluna em telas menores e em uma faixa única em desktop.
- A tabela mantém suas colunas em uma região horizontal rolável com nome e foco visível quando a largura não comporta todas.
- Busca, filtro e botões mantêm labels semânticos; paginação anuncia a contagem e o estado atual.
- Loading, falha, nenhum resultado e consulta sem contato têm mensagens explícitas.
- Nenhuma regra altera a fonte global ou a tipografia do produto.

## Segurança e persistência

- Cada leitura exige role RECEPCIONISTA no backend.
- A migration adiciona patients.phone nullable para não exigir backfill nem invalidar cadastro existente.
- Campo opcional rejeita telefone preenchido com número de dígitos diferente de 10 ou 11.
