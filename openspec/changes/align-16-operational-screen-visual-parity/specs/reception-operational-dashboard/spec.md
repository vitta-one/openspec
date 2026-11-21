## ADDED Requirements

### Requirement: O painel informa cancelamentos persistidos do dia
O painel de operação da Recepção MUST apresentar separadamente a quantidade de Consultas canceladas cuja data e horário pertencem ao dia atual no fuso configurado da clínica. A contagem MUST ser derivada dos registros persistidos e autorizada junto da projeção operacional existente; MUST NOT alterar a contagem de consultas não canceladas ou revelar identidade de paciente.

#### Scenario: Há consultas canceladas no dia
- **WHEN** o dia local possui uma ou mais Consultas canceladas
- **THEN** o painel apresenta a contagem real dessas Consultas em indicador próprio, além dos demais indicadores operacionais

#### Scenario: Não há cancelamentos no dia
- **WHEN** o dia local não possui Consulta cancelada
- **THEN** o indicador apresenta zero sem omitir sua categoria

#### Scenario: Limite do dia e autorização
- **WHEN** Consultas canceladas existem antes, dentro e depois do intervalo UTC correspondente ao dia local
- **THEN** somente as Consultas dentro do intervalo são contadas e o servidor disponibiliza o valor exclusivamente à role Recepcionista
