## 1. Especificação e desenho

- [x] 1.1 Atualizar a especificação consolidada para operação diária, dados limitados, busca, filtro e paginação.
- [x] 1.2 Atualizar o contrato de UX e registrar o motivo de não mostrar unidade/prontuário sem dados persistidos.

## 2. Dados e autorização

- [x] 2.1 Adicionar telefone brasileiro opcional ao modelo e migration sem backfill obrigatório.
- [x] 2.2 Expor busca rápida global de identidade e busca das consultas diárias, ambas protegidas no application service e sem conteúdo clínico.
- [x] 2.3 Projetar especialidades ativas associadas ao profissional sem atribuir uma especialidade fictícia à consulta.
- [x] 2.4 Cobrir fuso local, paginação de sete registros, cancelamentos, filtros, buscas, telefone opcional e RBAC.

## 3. Interface

- [x] 3.1 Trocar calendário/KPIs da home por tabela diária, busca global e contextual, filtro, status, ações e paginação.
- [x] 3.2 Manter fonte e tokens atuais; ampliar padding e espaçamento sem mudar o shell global.
- [x] 3.3 Cobrir carregamento, falha, lista vazia, foco e overflow em tela estreita.

## 4. Verificação

- [x] 4.1 Executar testes Python, validação OpenSpec e reflex compile --dry.
- [x] 4.2 Inspecionar a tela renderizada em desktop, tablet e viewport estreita; registrar achados em design-qa.md.
- [x] 4.3 Abrir PR para develop após resolver falhas de validação.
