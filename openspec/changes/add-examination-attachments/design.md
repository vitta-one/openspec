# Design — Exames e anexos (proposta não implementada)

## Contratos e responsabilidades

- UI Reflex: seleção de episódio autorizado, formulário e lista de exames; indicadores de estado sem dados fictícios.
- State: sessão/role, eventos e feedback; nunca carregar resultado de episódio alheio.
- Serviço de domínio: validar autoria, vínculo paciente/episódio, transições e metadados; auditoria transacional.
- Persistência prevista: entidades de solicitação, resultado, anexo e trilha de eventos, com FK para ClinicalCareRecord e Patient, migrations aditivas; modelos exatos só após revisão.
- Cloudinary: armazenamento privado, transformação/entrega somente com autorização no servidor; tokens e assinatura nunca na UI ou logs.

## Fluxos

1. Médico responsável em atendimento elegível cria pedido validado.
2. Resultado e anexo entram apenas após autorização e validação; banco guarda referência segura e integridade.
3. Histórico clínico autorizado apresenta resumo e anexos mediante URL temporária/entrega controlada.
4. Erro de Cloudinary, sessão expirada ou falha PostgreSQL mantém estado recuperável sem registro órfão ou acesso indevido.

## Segurança e concorrência

Validar extensão, MIME real, tamanho e limites; impedir scripts em conteúdo servido, vazamento de URLs, manipulação de IDs, callbacks/retries duplicados e exclusão inadvertida. Sanitizar nome exibido; não usar nome de arquivo como caminho confiável.

## Perguntas para Review

Confirmar atores autorizados, contratos de status, estratégia de upload, limites, retenção e política de download/remoção antes de gerar migrations e codificar.
