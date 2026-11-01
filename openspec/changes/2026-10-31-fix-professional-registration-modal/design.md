## Context

O Vitta One usa Python 3.12, Reflex 0.9.10.post2, PostgreSQL 16 e OpenSpec. O modal de `/admin/profissionais` e os formulários médicos de `/admin/funcionarios/novo` e `/admin/funcionarios/medico` já reutilizam `_professional_form_fields` e `AdminDirectoryState.save_professional`, que chama a mesma aplicação/serviço `register_medical_professional`.

## Decisions

1. Manter o modal existente, pois a spec de diretório exige edição/criação contextual. Não duplicar os serviços de cadastro nem mudar o framework.
2. `_validate_specialty_ids` retorna lista vazia para vínculo opcional; continua rejeitando IDs inexistentes ou inativos novos e removendo duplicados. As relações persistidas permanecem em `ProfessionalSpecialty` com constraint de unicidade.
3. Reutilizar validadores públicos de nome/e-mail do mesmo módulo de domínio no State antes de mutar; manter a validação definitiva e a autorização nos serviços server-side.
4. Reutilizar o checkbox Radix nativo, incluindo label clicável e teclado; CSS da linha deixa de criar um segundo retângulo decorativo.
5. Preservar `rx.dialog` para contenção de foco, Escape e restauração de foco próprios do Radix. O botão de fechar e o Cancelar chamam o mesmo evento que reseta estado. Bloquear fechamento durante a submissão.
6. Mensagem de primeiro acesso não promete envio. O estado pós-persistência continua discriminando provedor aceito, não configurado e indeterminado.
7. Quando a operação nasce do modal de Profissionais, atualizar dados e permanecer no diretório; na jornada de Funcionários, redirecionar à ficha criada.
8. Não alterar esquema de banco: o N:N já admite profissional sem associações.

## Risks / Mitigations

- A ausência de especialidade afeta filtros e exibição: mostrar estado textual explícito; sem alteração de agendamento.
- Regressão de edição: testar remoção total e preservação dos vínculos históricos inativos.
- Acessibilidade/foco em portal do Radix: validar com Chromium nos viewports alvo.
- Divergência entre ambientes: não declarar entrega de e-mail sem retorno do provedor.

## Validation

Executar OpenSpec strict, Pytest relevante/completo, `reflex compile --dry` e Chromium/teclado em 320, 390, 768, 1024 e 1440 px quando disponível. A change fica ativa até QA e revisão.
