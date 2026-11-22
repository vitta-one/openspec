## Why

A fila de espera ainda usa cards extensos, apresenta horário de entrada em UTC, não possui busca nem filtro contextual e confunde falha de consulta com fila vazia. Também faltava bloquear uma segunda entrada ativa do mesmo paciente nos dois fluxos de chegada.

## What Changes

- Exibir tabela operacional compacta em desktop e registros adaptados a celular.
- Exibir prioridade, paciente, entrada no fuso da clínica, tempo de espera, situação e ações existentes.
- Acrescentar busca por nome e filtro por prioridade preservando ordenação clínica no servidor.
- Mostrar última atualização, indicadores reais, loading, vazio, falha e filtros sem resultado.
- Permitir localizar o paciente no fluxo existente de inclusão sem duplicar serviços de entrada.
- Serializar inclusão avulsa e check-in por paciente no PostgreSQL para impedir duplicidade de entradas ativas.

## Capabilities

- MODIFIED: patient-reception-queue.
- Integração preservada: consultation-care-lifecycle.

## Fora do escopo

Triagem automática, novas categorias clínicas, nova API REST, polling, histórico paralelo, integrações externas ou migrations.
