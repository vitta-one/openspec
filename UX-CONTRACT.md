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

- Sidebar persistente à esquerda.
- Topbar compacto no conteúdo.
- O documento mantém a rolagem principal.
- Item ativo é identificado por contraste, texto e `aria-current`.

### Tela estreita

- A navegação vira faixa horizontal rolável acima do conteúdo.
- Nenhuma ação essencial depende de hover.
- Conteúdo retorna a uma coluna quando a divisão comprometer leitura.

## 4. Navegação por role

- Administrador: `/admin`.
- Recepcionista: `/recepcao`.
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

## 9. Pacientes, fila e módulos futuros

- Admin local visualiza pacientes/fila somente leitura.
- A tela local de Pacientes possui uma única busca no topo e pagina somente registros persistidos já autorizados para o preview.
- Alterar ou limpar a busca retorna para a primeira página; paginação nunca implica seleção de registros fora da página visível.
- A seleção de paciente usa checkbox controlado com cardinalidade máxima de 1. Selecionar outro paciente substitui a seleção anterior.
- Quando há seleção, uma barra contextual apresenta somente ações reais e somente leitura do preview, como consultar histórico e limpar a seleção.
- Mudar de página limpa a seleção para evitar contexto invisível; busca que elimina o paciente selecionado também limpa a seleção.
- Cadastro, localização, entrada, reavaliação e retirada continuam exclusivos da Recepção.
- Chamar/finalizar continua exclusivo do Médico.
- Agenda usa somente slots e Consultas persistidos. Até as capabilities correspondentes existirem, prontuário, diagnóstico, prescrição e Financeiro não inventam registros, totais ou transições.
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

## 11. Acessibilidade e estabilidade

- alvo WCAG 2.2 AA;
- foco visível;
- controles usam semântica nativa;
- controles de ícone possuem nome acessível;
- scrollbars permanecem visíveis;
- `prefers-reduced-motion` reduz transições;
- loading e feedback não deslocam ações principais desnecessariamente.
