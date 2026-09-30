# Vitta-One UX Contract

## 1. Escopo

Este contrato define o comportamento observável do login, shell autenticado e navegação local de QA. Ele complementa `DESIGN.md`; regras de domínio e autorização continuam pertencendo ao OpenSpec e às validações server-side.

## 2. Autenticação

- Login aceita e-mail + senha e não oferece cadastro público.
- Senha inicia mascarada.
- O controle de revelar senha é somente ícone e alterna `eye` / `eye-off`, `aria-label` e `aria-pressed` sem alterar o valor digitado.
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
- “Cancelar” restaura o formulário;
- desativar é reversível e nunca é apresentado como exclusão;
- listas são atualizadas após commit;
- erro server-side não apaga silenciosamente o que ainda precisa ser corrigido.

## 9. Pacientes, fila e módulos futuros

- Admin local visualiza pacientes/fila somente leitura.
- Cadastro, localização, entrada, reavaliação e retirada continuam exclusivos da Recepção.
- Chamar/finalizar continua exclusivo do Médico.
- Até as capabilities correspondentes existirem, Agenda, prontuário, diagnóstico, prescrição e Financeiro não inventam registros, totais, horários ou transições.
- Botões sem backend real não são renderizados como ações habilitadas.

## 10. Acessibilidade e estabilidade

- alvo WCAG 2.2 AA;
- foco visível;
- controles usam semântica nativa;
- controles de ícone possuem nome acessível;
- scrollbars permanecem visíveis;
- `prefers-reduced-motion` reduz transições;
- loading e feedback não deslocam ações principais desnecessariamente.
