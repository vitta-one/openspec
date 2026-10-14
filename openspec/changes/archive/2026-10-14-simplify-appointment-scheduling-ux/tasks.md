## Implementação
- [x] Estender projeção de slots com data/hora explícitas.
- [x] Agrupar horários no Admin e Recepção.
- [x] Separar inputs de data e hora para Administrador.
- [x] Simplificar copy/labels/estados sem mexer no domínio.
- [x] Validar o acesso dos perfis e o contrato de agendamento.

## QA
- [x] Testes de agrupamento, ordenação e ausência de data/hora.
- [x] OpenSpec strict, testes Python + PostgreSQL 16 e Reflex compile.
- [x] Verificação no navegador com teclado e 320/375/768px.
- [x] Arquivar apenas após evidências verificadas.

### Evidência de encerramento (2026-10-14)

- Código integrado à `develop` via PR #305.
- Gates automatizados: OpenSpec 10/10, Pytest 179 aprovados em PostgreSQL 16 descartável; Chromium com viewports 320/375/768 e fluxos de diretório/primeiro acesso/agenda.
- Requisitos sincronizados com `openspec/specs/` antes do arquivamento.
- Integração de e-mail real e homologação manual do Hackintosh são verificações de ambiente separadas, não comprovadas por estes testes.
