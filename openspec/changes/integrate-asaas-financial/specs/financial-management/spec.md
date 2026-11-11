# Spec Delta — Gestão financeira

## Purpose

Permitir gestão básica de cobranças da clínica com autorização no servidor, histórico verificável e projeções derivadas exclusivamente dos pagamentos persistidos.

## ADDED Requirements

### Requirement: Acesso financeiro autorizado
O sistema MUST revalidar sessão e role em toda leitura ou mutação financeira e MUST bloquear identidades com troca de senha pendente. Administrador e Financeiro MUST poder consultar, emitir e cancelar; somente Administrador MUST poder solicitar estorno integral Pix suportado. Recepcionista, Médico e Paciente MUST NOT receber dados financeiros internos.

#### Scenario: Ação direta sem permissão
- **GIVEN** sessão de Recepcionista, Médico ou Paciente
- **WHEN** uma operação financeira é chamada diretamente com identificador válido
- **THEN** o servidor nega acesso antes de retornar dados ou chamar o provedor.

#### Scenario: Sessão expirada ou provisória
- **WHEN** a sessão expira ou a senha inicial ainda exige troca
- **THEN** leituras e ações são negadas e a interface limpa os dados financeiros anteriores.

#### Scenario: Financeiro tenta estorno
- **GIVEN** a matriz de permissões aprovada
- **WHEN** Financeiro solicita estorno
- **THEN** o servidor recusa; Administrador pode prosseguir somente após confirmação explícita e validação da cobrança.

### Requirement: Cobrança vinculada a Consulta
O sistema MUST vincular cada cobrança a Consulta e paciente correspondentes, validar valor positivo em BRL com duas casas decimais e vencimento válido no fuso da clínica. MUST existir no máximo uma cobrança não cancelada/não estornada por Consulta, inclusive durante emissão incerta. Pagamento MUST NOT modificar o ciclo clínico.

#### Scenario: Emissão válida
- **GIVEN** Consulta existente e operador autorizado
- **WHEN** são informados valor válido, vencimento de hoje ou futuro e Pix ou boleto
- **THEN** a intenção persistida referencia o paciente da Consulta e o operador, sem aceitar outro paciente enviado pelo navegador.

#### Scenario: Emissão concorrente
- **WHEN** duas solicitações tentam cobrar a mesma Consulta simultaneamente
- **THEN** no máximo uma intenção elegível é criada e nenhuma segunda cobrança externa é emitida.

#### Scenario: Dados inválidos ou Consulta inexistente
- **WHEN** valor é zero, negativo, não finito, possui mais de duas casas, vencimento está no passado ou Consulta não existe
- **THEN** nenhuma chamada externa ocorre e o erro é apresentado sem expor dados pessoais.

#### Scenario: Consulta cancelada
- **GIVEN** uma Consulta com cobrança pendente
- **WHEN** o fluxo clínico cancela a Consulta
- **THEN** o estado financeiro permanece inalterado, com cancelamento financeiro separado e autorizado; nova emissão para Consulta cancelada é recusada.

### Requirement: Indicadores e evolução persistidos
O painel MUST calcular recebido, pendente, vencido e quantidade no banco, explicitando período e moeda. Recebido MUST somar valores brutos de cobranças RECEIVED pelo instante de recebimento; pendente e vencido MUST usar vencimento no período e estados elegíveis. Estornados/cancelados MUST ser excluídos dos totais monetários. Evolução MUST agrupar recebimentos por dia local. CONFIRMED MUST aparecer separado de recebido.

#### Scenario: Recorte conhecido
- **GIVEN** R$ 100 RECEIVED, R$ 80 PENDING, R$ 30 OVERDUE, R$ 20 CONFIRMED e R$ 50 REFUNDED no recorte
- **WHEN** o painel é consultado
- **THEN** exibe recebido R$ 100, pendente R$ 80, vencido R$ 30 e confirmação aguardando disponibilização R$ 20, com critérios temporais visíveis e sem somar o estorno aos recebidos.

#### Scenario: Banco vazio ou indisponível
- **WHEN** a consulta retorna zero cobranças ou falha
- **THEN** o painel mostra respectivamente zero real ou erro recuperável, sem trocar erro por zero e sem dados demonstrativos.

### Requirement: Pesquisa paginada e detalhes auditáveis
O painel MUST oferecer busca por nome de paciente, filtros combinados de estado e período, paginação estável de 20 itens e detalhe autorizado com identificador, paciente, Consulta, valor, vencimento, datas, método, situação, link e histórico. Histórico MUST identificar origem, momento e operador quando aplicável, sem permitir edição pelo navegador.

#### Scenario: Busca e filtros combinados
- **GIVEN** 25 cobranças compatíveis com paciente, estado e intervalo selecionados
- **WHEN** a listagem é solicitada
- **THEN** retorna 20 e depois 5 itens, sem repetição, em ordem de criação decrescente com desempate por identificador; total usa os mesmos filtros.

#### Scenario: Detalhe e histórico
- **WHEN** operador autorizado abre cobrança existente
- **THEN** vê as transições reais em ordem temporal, inclusive operações incertas; identificador inexistente produz estado não encontrado.

### Requirement: Interface financeira acessível e administração preservada
As rotas `/financeiro` e `/admin/financeiro` MUST reutilizar o design system, com labels, foco visível, estado textual, loading, erro, vazio e sucesso. A rota administrativa MUST exigir Administrador, independentemente da flag QA; demais previews MUST preservar seus guards. Operações sensíveis MUST exigir confirmação contextual.

#### Scenario: Celular e teclado
- **WHEN** o painel é usado em 390 px ou apenas por teclado
- **THEN** filtros, paginação, detalhes e confirmação permanecem alcançáveis sem rolagem horizontal para a tarefa principal.

#### Scenario: Administração sem preview QA
- **GIVEN** flag de preview local desativada
- **WHEN** Administrador abre `/admin/financeiro`
- **THEN** o acesso financeiro administrativo é permitido, sem liberar outros previews QA.
