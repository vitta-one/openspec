## Context

Consulte `proposal.md` para a motivação e os specs delta para o contrato observável. As 16 rotas usam o shell Reflex em `vitta_one/ui/components.py`, regras de negócio e projeções existentes, tokens de `assets/styles.css` e modelos persistidos. As integrações de Asaas e Resend, seus modelos, migrations, endpoints e workers já existem; esta implementação não deve duplicá-los.

## Goals / Non-Goals

**Goals:**

- Melhorar o shell compartilhado sem refazer os módulos de consulta, agenda, cadastro, fila ou prontuário.
- Adicionar projeções somente leitura que revalidam role no servidor e fornecem agregados não clínicos.
- Reutilizar os contratos de timezone da clínica e tokens atuais.
- Comparar visualmente todas as rotas com dados sintéticos em desktop e larguras menores.

**Non-Goals:**

- Alterar modelos, migrations, contratos de API ou regras clínicas/financeiras.
- Tratar aceitação do Resend como entrega, iniciar um worker automaticamente ou executar chamadas externas de produção.
- Criar endpoints web, aplicações frontend paralelas ou dados seed para a UI normal.

## Decisions

1. **Projeções isoladas com autorização explícita.** A leitura de Administração valida `ADMINISTRADOR` e agrega `Professional.is_active`, `Specialty.is_active`, `Consultation.scheduled_at/status` e contas `MEDICO`/`RECEPCIONISTA`. A leitura de e-mails valida `RECEPCIONISTA`, limita `EmailNotification.kind` a notificações de agenda e agrupa somente por `status`. Isso evita expor destinatários, dados clínicos e eventos financeiros. Alternativa considerada: calcular os números no state/frontend; descartada porque amplia o acoplamento e pode enfraquecer a autorização.

2. **Timezone e período explícitos.** O dia administrativo e os limites das 30 datas da Recepção são convertidos usando `clinic_date_range_to_utc`; o limite final é exclusivo. O período local inclui hoje e os 29 dias anteriores. Alternativa considerada: subtrair 30×24 horas em UTC; descartada porque cruza datas locais de maneira inesperada.

3. **Shell deriva seu padrão do perfil e guarda a preferência do usuário.** A sidebar usa estado ainda não escolhido até resolver o perfil autenticado; nessa condição, Médico e Paciente mantêm a navegação expandida atual, enquanto Recepção, Administração e Financeiro iniciam compactos. Após uma escolha manual, o estado é mantido nas rotas do mesmo perfil. Uma mudança de perfil reavalia o padrão. Alternativa considerada: definir um único booleano global como padrão; descartada porque deixa uma variante visual incorreta para parte dos perfis.

4. **Decoração vetorial local, sem rasterização das referências.** Os cabeçalhos usam uma ilustração SVG autoral e decorativa como superfície visual compartilhada; a variante médica recebe a arte de consultório. O texto, botões e conteúdos permanecem componentes Reflex independentes, e a arte é ignorada por leitores de tela. Alternativa considerada: usar as imagens PNG como fundo; descartada por esconder conteúdo e violar a função de referência.

5. **Nenhuma migration ou dependência nova.** Os agregados são derivados em leitura de tabelas existentes; os indicadores da Recepção mapeiam `ACCEPTED`, `DELIVERED`, `FAILED` e `PENDING/SENDING/UNKNOWN/NOT_CONFIGURED`, excluindo `SUPPRESSED`. O código do provedor não muda. Alternativa considerada: persistir contadores ou criar tabela de métricas; descartada por risco de divergência e falta de necessidade para os volumes previstos.

## Risks / Trade-offs

- **Cabeçalhos compartilhados afetam telas fora das 16 rotas** → aplicar classes e arte somente dentro do shell autenticado, verificar as rotas-alvo e revisar páginas já existentes que usam o mesmo helper.
- **Preferência de sidebar pode persistir entre logins da mesma role no mesmo state** → comparar com o perfil corrente e testar login/logout, navegação interna e alternância manual; não persistir essa preferência no banco.
- **Agregados contam notificações por registro, não destinatários únicos nem mensagens na caixa de entrada** → rotular exatamente cada estado e período; não afirmar entrega sem evento `DELIVERED` autenticado.
- **Imagens decorativas podem se sobrepor a ações em larguras intermediárias** → usar posição absoluta com `pointer-events: none`, respeitar área de texto/ações e validar 320–1768 px.
- **Não há credenciais de sandbox nem URL pública de webhook para a execução local** → manter os testes de provedores em mocks e declarar a homologação externa pendente; a change não altera integrações.

## Migration Plan

1. Publicar as mudanças de leitura/UI junto com os arquivos SVG e os testes; não há migration de banco.
2. Reversão: reverter os commits desta change, preservando as tabelas existentes e os eventos persistidos de Asaas/Resend.
3. Não há operação de implantação externa, configuração de segredo ou migração de dados nesta change.
