# Diretório operacional de pacientes da Recepção

## Why

A listagem atual usa cards extensos, ação de navegação ambígua e paginação visível mesmo com apenas uma página. O feedback de erro é transitório e a busca de diretório não aceita telefone, embora a busca rápida existente aceite. O estado Reflex pode manter a projeção do diretório após uma falha de autorização.

## What Changes

- Substituir os cards por tabela semântica compacta com nome, telefone e ação "Ver detalhes".
- Preservar o cadastro e a ficha individual nas rotas já existentes.
- Aplicar busca explícita por nome, CPF ou telefone, usando dados persistidos com paginação no SQL.
- Ajustar pluralização, paginação contextual, estados de carregamento/erro/vazio, limpeza e restauração de busca.
- Limpar a projeção protegida do diretório ao invalidar autorização.
- Manter o visual e a responsividade do design system.

## Impact

- UI: `vitta_one/ui/patient_directory_components.py`, `assets/styles.css`.
- State: `vitta_one/patient_queue/state.py`.
- Aplicação: `vitta_one/patient_queue/application.py`.
- Testes de regressão: `tests/test_reception_patient_directory.py`.
- Sem migrations, dependências adicionais ou novos endpoints REST.
- Nenhuma mudança de autorização para Administrador, Médico ou Paciente.
