# Design técnico — Cadastro de novo paciente

## Decisões

1. **Preservar domínio e segurança.** `reception_create_patient` continua exigindo `RECEPCIONISTA` no servidor e delega validação/persistência ao serviço existente. A constraint `UNIQUE` no CPF é a garantia final de unicidade. Não será criada API REST.
2. **Máscara é apresentação, não validação.** Handlers Reflex normalizam a apresentação do CPF e do telefone para digitação/colagem. O serviço verifica o CPF original antes de normalizar e persistir, evitando aceitar caracteres inválidos que seriam descartados silenciosamente em chamadas diretas.
3. **Erros associados a campos.** O State mantém mensagens individuais por campo; o formulário expõe `aria-invalid`, `aria-describedby`, regiões de alerta e foco no primeiro inválido. O servidor sempre revalida, independentemente do comportamento do navegador.
4. **Sucesso recuperável.** Após `commit`, o State memoriza o ID criado, apresenta sucesso e redireciona à rota existente `/recepcao/pacientes/[patient_id]`. Se a navegação falhar, o link permanece disponível e o State bloqueia outra criação na mesma instância do formulário.
5. **CPF existente.** A exceção de duplicidade só é obtida após autorização. A UI informa duplicidade sem expor CPF ou outros dados no alerta e só oferece link por ID autorizado, cuja ficha também é protegida no servidor.
6. **Interface canônica.** `section_panel`, `field_label`, `feedback_region`, `vitta-input`, links e botões do projeto são reutilizados; a largura máxima local é 44rem e o layout mobile usa uma coluna.
7. **Carregamento focado.** A rota de criação inicializa apenas o formulário; não consulta a fila sem necessidade. Eventos existentes de busca, agendamento, cadastro e ficha continuam separados.

## Fluxo

```text
Recepção → Pacientes → Novo paciente → validação
                                  ├─ erro campo → editar mantendo os valores
                                  ├─ CPF duplicado → link à ficha autorizada
                                  └─ commit → sucesso → ficha do paciente
                                              └─ navegação falha → link de recuperação
```

## Consistência e proteção

- CPF em banco: 11 dígitos. Máscara somente para interface.
- Telefone em banco: ausente ou 10/11 dígitos segundo contrato atual.
- Nenhum dado pessoal é enviado em query string ou mensagens de erro técnicas.
- A ação de cadastro não cria fila, agendamento ou dados clínicos.
- O ID salvo não é reutilizado automaticamente para novo `INSERT`.
- Não presumir que a navegação/feedback pós-commit caracteriza rollback.

## Validação planejada

- Pytest de máscaras, nome, CPF, telefone opcional/inválido, persistência, duplicidade e caracteres inválidos.
- Validação OpenSpec strict e `reflex compile --dry`.
- QA Chromium: digitar e colar, Enter, foco, clique duplo, duplicidade, erros de persistência, sessão expirada, acesso negado e viewports 320/390/768/1024/1440.
- PostgreSQL de QA isolado: verificar concorrência e unicidade sem alterar dados de trabalho.
