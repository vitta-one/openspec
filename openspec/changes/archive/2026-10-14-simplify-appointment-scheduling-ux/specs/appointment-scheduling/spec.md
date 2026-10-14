## ADDED Requirements

### Requirement: Horários são apresentados por dia em linguagem operacional
O sistema MUST mostrar horários reais agrupados por data local da clínica, identificando hora, profissional e situação textual. A interface de Administração e Recepção MUST evitar termos técnicos como "slot" para orientar o usuário.

#### Scenario: Dias e profissionais diferentes
- **WHEN** há horários futuros em vários dias e profissionais
- **THEN** a interface os agrupa por data, mantendo hora e profissional em cada item e ordenação temporal

#### Scenario: Sem horários no filtro
- **WHEN** o período escolhido não contém horários disponíveis
- **THEN** o sistema apresenta orientação simples para alterar período ou profissional, sem criar dados fictícios

### Requirement: Cadastro de horário usa data e hora separadas
O Administrador MUST informar profissional, data e hora em campos independentes, com labels e validação acessível; o backend MUST manter o mesmo contrato de horário local e unicidade do domínio.

#### Scenario: Horário válido
- **WHEN** o Administrador escolhe profissional ativo, data futura e hora
- **THEN** a aplicação combina os valores no horário local da clínica e persiste a disponibilidade usando o serviço autorizado existente

#### Scenario: Data ou hora ausente
- **WHEN** o Administrador tenta salvar sem data ou sem hora
- **THEN** recebe erro legível e nenhum horário parcial é persistido

#### Scenario: Horário duplicado
- **WHEN** o Administrador escolhe profissional e data/hora já cadastrados
- **THEN** o serviço existente rejeita o conflito sem criar duplicidade
