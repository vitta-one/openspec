# Vitta-One UX Contract

## Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Select/Listbox | Reflex/Radix shared select primitive | DESIGN.md + UX-CONTRACT.md | authored | keyboard + popup compile |
| Form | Shared field/feedback primitives in `vitta_one/ui/components.py` | DESIGN.md + UX-CONTRACT.md | create / edit / login | unit + compile + manual flow |
| Scrollbar | Global rules in `assets/styles.css` | DESIGN.md | document / bounded list | CSS audit + narrow viewport |
| CRUD | Professional directory state + shared feedback contract | OpenSpec + UX-CONTRACT.md | create / edit / deactivate-reactivate | unit + authorization + manual full flow |
| Agenda | Appointment scheduling State + Reflex/Radix controls | OpenSpec appointment-scheduling + UX-CONTRACT.md | admin availability / reception scheduling | unit + PostgreSQL locking + compile + manual flow |

## 1. Escopo

Este contrato define o comportamento observável do login, shell autenticado e navegação local de QA. Ele complementa `DESIGN.md`; regras de domínio e autorização continuam pertencendo ao OpenSpec e às validações server-side.

## 2. Autenticação

- Login aceita e-mail + senha e não oferece cadastro público.
- Senha inicia mascarada.
- O controle de revelar senha é somente ícone e alterna `eye` / `eye-off`, `aria-label` e `aria-pressed` sem alterar o valor digitado.
- O controle de revelar senha permanece centralizado verticalmente dentro do campo e conserva alvo clicável estável.
- Em viewports estreitos ou baixos, o formulário de login mantém todos os campos e a ação Entrar alcançáveis; o painel visual secundário pode ser reduzido ou ocultado antes de comprimir a tarefa principal.
- Submit duplicado é bloqueado durante autenticação.
- Credenciais inválidas retornam mensagem genérica inline.
- Sessão válida redireciona para o dashboard autorizado; logout revoga a sessão antes do redirecionamento.
- Password managers e colagem permanecem permitidos.

## 3. Shell autenticado

### Desktop

- Sidebar persistente à esquerda e recolhível em trilho de ícones, sem remover destinos ou perder seus nomes acessíveis.
- Topbar compacto com controle de menu e indicação curta do contexto operacional; sem duplicação de conta ou estado decorativo de sessão.
- A região de conta e logout fica no rodapé da sidebar e usa os dados da sessão validada.
- O documento mantém a rolagem principal; a lista de navegação pode rolar quando necessário.
- Item ativo usa contraste, texto e `aria-current="page"`; a seção administrativa ancestral tem destaque mais discreto e não recebe `aria-current`.
- Rotas profundas como `/admin/funcionarios/novo` mantêm Funcionários selecionado, enquanto o breadcrumb identifica a página específica.

### Tablet e celular (até 1050 px)

- A navegação é um único drawer temporário, acessado pelo hamburger, sem segunda sidebar ou faixa horizontal redundante.
- O drawer possui fechamento visível, Escape, foco mantido dentro enquanto aberto e foco restaurado ao acionador após fechar.
- Com o drawer aberto, o conteúdo principal fica inerte e o scroll de fundo é bloqueado; redimensionar não aprisiona o foco.
- Nenhuma ação essencial depende de hover.
- Conteúdo retorna a uma coluna quando a divisão comprometer leitura.
- O layout não pode gerar overflow horizontal em 320, 390, 768, 1024 ou 1440 px.

### Navegação e permissões

- O menu é montado a partir das rotas existentes de cada role, sem ampliar a autorização do servidor.
- A Administração contém sua página inicial e os destinos de Funcionários, Profissionais, Especialidades, Horários e Configurações.
- Visualizações locais de QA formam grupo separado, visível apenas com a configuração autorizada; não oferecem permissão de mutação clínica ao Administrador.
- As páginas e eventos continuam sujeitos ao RBAC e à validação de sessão no servidor.

## 4. Navegação por role

- Administrador: `/admin`.
- Recepcionista: `/recepcao` (dashboard), `/recepcao/agenda`, `/recepcao/pacientes`, `/recepcao/fila`. Cada rota revalida sessão e role no servidor.
- Médico: `/medico`.
- Financeiro: `/financeiro`.
- A tentativa de acessar outra role mantém a resposta de acesso negado.
- Ocultar link nunca substitui autorização server-side.

## 5. Modo local de QA do Administrador

O modo local só existe quando `VITTA_ONE_LOCAL_ADMIN_PREVIEW=true`.

Rotas de inspeção:

- `/admin/recepcao`
- `/admin/agenda`
- `/admin/atendimento`
- `/admin/pacientes`
- `/admin/financeiro`

Regras:

- a sessão precisa continuar sendo `ADMINISTRADOR`;
- cada loader revalida flag + sessão + role antes de consultar dados;
- o modo é identificado visualmente como “Modo local de QA”;
- dados existentes são apresentados somente leitura;
- handlers de Recepção/Médico não são reutilizados para conceder mutações ao Admin;
- módulos ainda não implementados exibem estado vazio ou estrutura desabilitada, sem dados simulados;
- quando o flag está falso, as rotas de preview não retornam dados e redirecionam ao `/admin`.

## 6. Feedback

- erro corrigível: inline, próximo ao fluxo que falhou;
- sucesso: região `status` estável;
- loading: indicador em região reservada;
- empty state: explica o que falta e só oferece ação quando ela realmente existe;
- nenhuma informação crítica existe apenas em toast.

## 7. Forms

- campos possuem labels reais;
- formulários de produto desativam validação nativa e mantêm mensagens do app;
- erro preserva valores editáveis relevantes;
- campos inválidos usam texto e associação acessível;
- textareas usam `resize: none`;
- Select reutiliza Reflex/Radix;
- segredos nunca aparecem em URL, logs ou feedback.

## 8. CRUD administrativo

- criar/editar mantém o contexto da Administração;
- criação e edição de especialidade/profissional usam diálogos modais controlados pelo State; o diretório permanece como superfície principal;
- o diálogo permanece aberto quando a validação server-side falha e fecha somente após sucesso persistido ou cancelamento explícito;
- Escape/fechamento do diálogo usa o primitive Reflex/Radix e restaura foco ao fluxo de origem;
- formulários longos em diálogo possuem altura limitada à viewport e rolagem interna, mantendo ações alcançáveis;
- “Cancelar” restaura o formulário;
- desativar é reversível e nunca é apresentado como exclusão;
- listas são atualizadas após commit;
- erro server-side não apaga silenciosamente o que ainda precisa ser corrigido.

### Diretórios completos e resumo administrativo

- O painel `/admin` consulta e mostra somente os três últimos profissionais e as três últimas especialidades, por data de cadastro e ID; detalhes completos são carregados apenas na página correspondente ou na abertura de formulário.
- Os links “Ver todas” e “Ver todos” navegam para `/admin/especialidades` e `/admin/profissionais`, com as mesmas verificações server-side da role Administrador.
- As páginas completas têm busca, filtro e paginação; mudanças de filtro reiniciam a página. A paginação inicial é no State e deve ser trocada por paginação SQL quando o volume exigir.
- Só botões e links acionáveis exibem cursor pointer, foco visível e feedback de hover; informação não interativa não simula clique.
- O dashboard conserva os diálogos existentes, sem duplicar validações ou operações de domínio.

### Cadastro e primeiro acesso de Médicos

- “Novo profissional” solicita nome, e-mail e especialidades; o servidor gera o identificador interno e cria ou reutiliza a identidade Médica quando autorizado.
- A senha inicial é aleatória, temporária e nunca aparece em interface, armazenamento client-side ou logs. O primeiro login leva à troca obrigatória em `/primeiro-acesso` e não libera operações clínicas até a rotação.
- Credenciais expiram em 24 horas; o Resend é usado exclusivamente no servidor e pode estar desconfigurado. A tela distingue “e-mail aceito pelo provedor” de “não enviado”/“envio não confirmado”, sem inferir entrega na caixa postal.
- Reemissão requer confirmação explícita do Administrador, invalida a senha provisória anterior e não ocorre automaticamente após timeout.

## 9. Pacientes, fila e módulos futuros

- Admin local visualiza pacientes/fila somente leitura.
- A tela local de Pacientes possui uma única busca no topo e pagina somente registros persistidos já autorizados para o preview.
- Alterar ou limpar a busca retorna para a primeira página; paginação nunca implica seleção de registros fora da página visível.
- A seleção de paciente usa checkbox controlado com cardinalidade máxima de 1. Selecionar outro paciente substitui a seleção anterior.
- Quando há seleção, uma barra contextual apresenta somente ações reais e somente leitura do preview, como consultar histórico e limpar a seleção.
- Mudar de página limpa a seleção para evitar contexto invisível; busca que elimina o paciente selecionado também limpa a seleção.
- Cadastro, localização, entrada, reavaliação e retirada continuam exclusivos da Recepção.
- Chamar/finalizar continua exclusivo do Médico.
- Agenda usa somente slots e Consultas persistidos. Atendimento clínico, Prescrições e histórico usam somente registros persistidos (`ClinicalCareRecord`, `Prescription` e `PrescriptionItem` quando aplicáveis); exames e Financeiro continuam sem dados fictícios enquanto suas capabilities não forem implementadas.
- Botões sem backend real não são renderizados como ações habilitadas.

## 10. Agenda e disponibilidade

- A disponibilidade é exibida como **slots explícitos de data/hora**; a UI não presume duração, recorrência ou intervalos clínicos.
- Administrador cria, filtra, desativa e reativa slots em `/admin`; slot reservado não oferece ação administrativa de desativação.
- Recepção consulta agenda por profissional/período, localiza paciente existente, agenda, reagenda e cancela Consultas em `/recepcao`.
- Busca de paciente reutiliza a identidade persistida existente; não existe cadastro paralelo para agenda.
- Agendamento exige paciente selecionado + slot futuro disponível e preserva seleção quando um conflito concorrente ocorre.
- Reagendamento usa diálogo explícito, preserva o paciente e só confirma depois da seleção de outro slot disponível.
- Cancelamento usa confirmação explícita, nunca exclui fisicamente a Consulta e mantém o registro no histórico.
- Estados de slot e Consulta aparecem em texto; cor é apenas sinal secundário.
- Filtros e tarefas principais retornam a uma coluna em tela estreita, sem exigir rolagem horizontal.
- Horários são recebidos/exibidos no timezone IANA configurado da clínica e persistidos em UTC.
- A ação **Confirmar chegada** existe somente para Consulta `AGENDADA` e representa chegada presencial confirmada pela Recepção; não representa confirmação antecipada por mensagem.
- Confirmar chegada solicita sintomas + prioridade informados manualmente e cria a entrada de fila vinculada sem trocar o paciente da Consulta.
- Consulta `CONFIRMADA` aparece como paciente já colocado na fila; reagendamento/cancelamento direto da Agenda deixam de ser ações válidas após essa etapa.
- Consulta agendada na fila é elegível somente ao Médico vinculado ao profissional marcado; atendimentos avulsos continuam seguindo a fila compartilhada.
- Ao Médico chamar uma Consulta confirmada, a UI passa a refletir `EM_ANDAMENTO`; ao finalizar, `CONCLUIDA`.
- Retirar da fila uma Consulta confirmada cancela a Consulta e preserva o histórico; retirar walk-in não altera Agenda.
- O painel Médico identifica a origem “Consulta agendada” e mostra horário/profissional já persistidos, sem antecipar prontuário.
- O preview local do Admin permanece somente leitura e pode exibir timestamps do lifecycle real.

### Exibição diária dos horários

- Horários reais da agenda são agrupados por dia no fuso configurado, com hora, profissional e situação legíveis; o usuário não precisa conhecer o termo “slot”.
- A Administração escolhe profissional, data e hora em controles separados, mantendo as validações e a persistência UTC existentes.
- A Recepção preserva as regras de reserva, chegada, reagendamento e cancelamento e visualiza as opções disponíveis agrupadas por dia, sem geração de intervalos ou recorrências automáticas.

## 11. Atendimento clínico e histórico

- O formulário clínico aparece quando o Médico possui atendimento ativo, seja Consulta agendada confirmada, seja passagem direta da fila de pronto-socorro.
- Walk-in recebe um `ClinicalCareRecord` vinculado exclusivamente ao `QueueEntry` sob o mesmo claim transacional; agendamentos preservam o vínculo à `Consultation`.
- O formulário possui quatro áreas: queixa principal, anamnese, diagnóstico e conduta/observações.
- Os campos aceitam salvamento parcial e preservam o texto local quando um erro corrigível ocorre.
- O estado textual **Salvo** / **Alterações não salvas** é a fonte primária de feedback do rascunho.
- O fluxo normal de **Finalizar atendimento** fica indisponível enquanto houver alterações locais não salvas; o Médico pode salvar ou descartar o rascunho para continuar. A confirmação é precedida por uma etapa de revisão de dados persistidos, antes do commit de finalização.
- Textareas clínicas são a variante longa do formulário: mantêm foco visível e permitem `resize: vertical`; demais textareas do produto preservam o comportamento canônico existente.
- O histórico clínico é somente leitura, inclui somente Consultas concluídas e usa paginação server-side de 10 registros.
- O Médico acessa histórico somente no contexto do paciente do atendimento ativo autenticado.
- Ao finalizar, perder autorização ou encerrar sessão, o State remove formulário e histórico clínico sensível.
- O Admin QA local pode projetar histórico clínico persistido e Atendimento ativo somente em modo explicitamente habilitado e sem ações de edição.
- Conteúdo clínico não é colocado em URL, log, mensagem de erro, toast detalhado ou telemetria.
- Prescrições são uma seção própria do Atendimento; exames, anexos, assinatura digital e financeiro permanecem em capabilities separadas.

## 12. Prescrições e impressão

- A seção **Prescrições** aparece para Atendimento ativo com `ClinicalCareRecord`, tanto agendado quanto de pronto-socorro.
- Um Atendimento pode possuir múltiplas Prescrições; cada documento é criado já com o primeiro item válido.
- Cada item mostra medicamento/item como conteúdo principal, orientação/posologia logo abaixo e observações somente quando existirem.
- “Nova prescrição”, adicionar/editar item e editar observações gerais usam dialogs controlados, com labels visíveis, limites refletidos nos campos e valores preservados em erro corrigível.
- Remover o último item isoladamente não é permitido; o Médico deve excluir a Prescrição inteira enquanto a Consulta ainda está `EM_ANDAMENTO`.
- Exclusão de documento e remoção de item usam confirmação própria da aplicação; não usam `window.confirm`.
- Operações de Prescrição são explícitas e persistidas imediatamente; não compartilham o dirty state do formulário de Atendimento.
- O fluxo normal de **Finalizar atendimento** fica indisponível enquanto uma operação de Prescrição estiver em andamento.
- Prescrições de Consultas concluídas aparecem no histórico como conteúdo somente leitura e ficam recolhidas por padrão para evitar expansão excessiva.
- A visualização de impressão vive em rota protegida, sem shell operacional, e pode ser reaberta pelo Médico autor depois da conclusão.
- A versão imprimível exibe paciente, profissional, registro profissional, data/hora do atendimento (instante agendado para Consulta, chamada real para pronto-socorro), itens e observações gerais.
- A versão imprimível sempre informa **“Documento sem assinatura digital nesta etapa.”** e não mostra selo, QR Code ou indicadores ZapSign.
- O Admin QA local projeta Prescrições reais em Atendimento/histórico somente leitura; fora da flag local não existe API clínica geral para Administrador.
- Conteúdo de Prescrição não entra em URL, logs, mensagens de erro detalhadas ou telemetria.

## 13. Acessibilidade e estabilidade

- alvo WCAG 2.2 AA;
- foco visível;
- controles usam semântica nativa;
- controles de ícone possuem nome acessível;
- scrollbars permanecem visíveis;
- `prefers-reduced-motion` reduz transições;
- loading e feedback não deslocam ações principais desnecessariamente.

## 14. Área modular de Recepção

- A navegação da Recepção mantém Visão geral, Agenda, Pacientes e Fila com as rotas e permissões existentes.
- A página inicial de Recepção é a tabela **Recepção — Operação do Dia**, com o dia definido no fuso configurado da clínica e as consultas persistidas nesse intervalo local, em ordem de horário.
- A tabela mostra horário, nome e telefone do paciente, profissional, especialidades ativas cadastradas para esse profissional, situação persistida e acesso à Agenda. A especialidade não é vinculada diretamente à Consulta nesta etapa; várias especialidades ativas aparecem juntas. Quando não existe especialidade ou telefone cadastrado, a interface informa a ausência sem criar um valor fictício.
- O telefone é opcional no cadastro do paciente. Os registros existentes permanecem válidos sem telefone e mostram “Telefone não informado”.
- A busca rápida global do topo localiza pacientes por nome, telefone ou CPF e retorna somente identidade mínima para a rota Pacientes. A busca da tabela e o filtro por profissional operam somente sobre consultas do dia. A tabela é paginada no servidor em grupos de sete; aplicar busca ou trocar profissional reinicia a paginação.
- Consultas canceladas permanecem na tabela e exibem o status persistido. A recepção não deduz falta, urgência, chegada, duração ou disponibilidade pelo horário.
- “Ir para Agenda” navega para a Agenda; “Nova consulta” abre o mesmo modal compartilhado com a Agenda, sem criar lógica paralela de reserva ou check-in.
- A leitura inicial mostra carregamento; uma falha limpa dados protegidos e permite tentar novamente; a atualização é manual e exibe quando a última leitura terminou. Não há promessa de tempo real.
- Os controles de busca, filtro, paginação e acesso à Agenda mantêm rótulos acessíveis, foco visível, operação por teclado e tabela horizontalmente contida em telas estreitas, sem ampliar o documento.
- A tela não mostra conteúdo clínico, prontuário ou unidade não configurada.


## 15. Administração por tarefas e legibilidade global

- `/admin` concentra **navegação**, não renderiza simultaneamente formulários de clínica, funcionários e horários.
- `/admin/funcionarios` apresenta somente os perfis com cadastro suportado pelo back-end: Médico e Recepcionista. Não oferece falsas opções para Administrador ou Financeiro.
- `/admin/funcionarios/medico` reutiliza formulário, verificações de especialidades, validação e persistência de `AdminDirectoryState`; o formulário tem navegação de volta e feedback recuperável sem depender de modal.
- `/admin/funcionarios/recepcionista` reutiliza `AdminStaffState` e mantém a exigência de senha inicial; informações sensíveis nunca aparecem na URL.
- `/admin/profissionais` e `/admin/especialidades` continuam como diretórios para busca, filtro, edição e controle de situação.
- `/admin/horarios` separa em abas semânticas o **expediente semanal**, os **horários avulsos** e a **consulta dos horários**. Cada operação preserva os serviços, timezone e validações já existentes.
- `/admin/configuracoes` apresenta apenas as configurações da clínica existentes, sem expor um formulário paralelo no dashboard.
- `/recepcao/agenda` mantém **Consultas do período** como conteúdo principal e abre **Agendar consulta** em modal, com paciente previamente selecionado quando originado da ficha. A rota legada `/recepcao/agenda/nova` mostra a mesma Agenda com o modal aberto. O estado é controlado e não depende de aba invisível ou valor de rota sensível.
- Todas as novas subrotas exigem `AuthState.load_protected` e `protected_workspace` com `verified_path`; autorização de negócio permanece no servidor.
- Campos, placeholders, selects, menus portaled, badges e mensagens devem manter texto legível com contraste normal de pelo menos 4,5:1 e controles com foco visível. Estados desabilitados permanecem distinguíveis sem depender exclusivamente da cor.
- Tarefas são verificadas em 320, 375, 768 e 1280 px com foco, navegação por teclado, ausência de overflow e fluxos reais. Testes estáticos e `reflex compile --dry` não substituem QA visual.
