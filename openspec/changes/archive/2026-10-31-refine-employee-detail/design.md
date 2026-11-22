## Decisões técnicas

- Conservar `/admin/funcionarios/[employee_id]`, `AdminStaffState` e `protected_workspace` em Reflex.
- `get_employee_detail` mantém `require_role(ADMINISTRADOR)` e retorna somente projeção administrativa. Usa `User.display_name`; caso ausente em Médico vinculado, reutiliza `Professional.name`. Na ausência de ambos, exibe “Nome não informado” sem transformar e-mail em nome.
- O vínculo é consultado por `Professional.user_id`, e as especialidades por `ProfessionalSpecialty` e `Specialty`. Nenhuma informação profissional será fabricada ou armazenada novamente.
- `detail_status` explicita carregamento, sucesso, ausência e erro. A comparação do ID com a rota impede renderizar registros de outra navegação; erro mantém tentativa de recarregar.
- UI usa `page_header`, `breadcrumb`, `section_panel`, `empty_state` e `error_banner`, com container de leitura e flex responsivo.
- Edição de funcionários não é exposta sem transação e autorização próprias. Para Médico com vínculo, a ficha direciona ao diretório profissional existente.

## Segurança e compatibilidade

Não expor hashes, tokens, sessões ou dados clínicos. Manter criação e listagem, sem mudanças de schema/migrations ou APIs REST. Testar autorização por role e sessão revogada.

## Qualidade

Executar testes específicos, suíte Python, compilação Reflex e inspeção de 320/390/768/1024/1440 px quando houver runner adequado. Ausência de runner deve ficar explícita na PR.
