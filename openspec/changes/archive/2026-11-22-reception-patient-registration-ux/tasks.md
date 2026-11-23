# Tarefas — Cadastro de novo paciente

## Implementação

- [x] Inspecionar a rota, UI, State, serviço, modelo e restrição de CPF existentes.
- [x] Ajustar largura, hierarquia e botões para desktop/mobile.
- [x] Adicionar máscara visual de CPF e telefone com colagem sem pontuação.
- [x] Exibir erros individuais e preservar dados após falha.
- [x] Tratar CPF já existente com link à ficha autorizada.
- [x] Impedir repetição enquanto salva e depois do commit confirmado.
- [x] Preservar abertura automática da ficha e oferecer recuperação se a navegação falhar.
- [x] Corrigir o serviço para validar CPF bruto antes da normalização.
- [x] Adicionar regressões unitárias de máscara, validação e CPF inválido.

## Homologação pendente de evidência

- [ ] Validar esta change com OpenSpec strict na CI ou ambiente local.
- [ ] Executar Pytest completo e `reflex compile --dry`.
- [ ] Executar migrações existentes apenas em PostgreSQL QA isolado; nenhuma migration nova é necessária.
- [ ] Confirmar foco, teclado, colagem e ausência de overflow em Chromium (320/390/768/1024/1440).
- [ ] Exercitar clique duplo, CPF duplicado e concorrência em PostgreSQL QA.
- [ ] Revisar o PR, concluir QA e arquivar a change após aprovação.
