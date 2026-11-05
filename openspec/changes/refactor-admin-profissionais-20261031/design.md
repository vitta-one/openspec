## Contexto

A rota administrativa já possui busca e filtros sobre projeção autorizada por `admin_list_professionals`, paginação no State, formulário modal e serviço de onboarding do Resend. O contrato vigente preserva Reflex/Radix e a linguagem de estação clínica de `DESIGN.md`.

## Decisões

1. Reutilizar `rx.table`, formulário e `AdminDirectoryState` existentes; em telas estreitas, usar lista compacta sem cards ou overflow de página.
2. Reaproveitar filtros em memória e paginação atual (10 por página); por enquanto as consultas do banco são feitas ao carregar ou após mutações, não a cada tecla. A migração para paginação SQL depende de volume e medições.
3. Ler nomes e vínculos exclusivamente dos serviços existentes. Exibir primeira especialidade e um popover acessível para as restantes; sem especialidade, exibir “Não vinculada”.
4. Diferenciar `PENDING`, `ACCEPTED`, `FAILED`, `UNKNOWN`, `NOT_CONFIGURED` e `NOT_REQUIRED` apenas quando persistidos. Não afirmar entrega na caixa de entrada.
5. Alterar status em duas etapas: seleção na UI, confirmação explícita e escrita no servidor com pré-condição `expected_active`, sob `SELECT FOR UPDATE`. A conta vinculada permanece independente.
6. Permitir lista vazia em `_validate_specialty_ids` conservando validação de IDs informados, especialidades ativas e atomicidade do cadastro.
7. Manter token, senha inicial e resposta do provedor no servidor. Em exceção de transporte, registrar resultado indeterminado, sem repetir automaticamente o envio.

## Riscos

- A página ainda busca a lista completa autorizada no carregamento. A migração para filtro/paginação SQL deve ser planejada quando o volume justificar.
- Atualização da regra “ao menos uma especialidade” exige revisão de quem depende dessa garantia.
- Envio real Resend não pode ser homologado sem ambiente configurado; nunca testar com dados de pacientes reais.

## QA obrigatório

OpenSpec strict; Pytest do diretório/onboarding e suíte; `reflex compile --dry`; navegador/teclado em 320, 390, 768, 1024 e 1440 px. Sem executar migration em ambiente persistente.
