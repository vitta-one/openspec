## Contexto

Reflex usa `AdminClinicConfigurationState` para mostrar uma leitura do ambiente, e `PatientPortalState` usa `clinic_location()` na abertura da agenda. A página não possui ação de salvamento.

## Decisões

1. Criar `ClinicConfiguration` com `id=1` protegido por CHECK e `revision` crescente. Uma migration aditiva em Alembic cria a tabela; não inserir valores fictícios.
2. Criar `ClinicConfigurationChange` como registro histórico na mesma transação da gravação. Não registrar mudanças nulas.
3. Centralizar leitura/gravação em `clinic_settings/service.py`. `get_clinic_location(db)` consulta banco primeiro; só usa `VITTA_ONE_CLINIC_NAME/ADDRESS` quando não existe registro. Depois do primeiro salvamento, as variáveis não substituem dados.
4. `save_clinic_location()` revalida sessão e role Administrador, normaliza, valida limites, bloqueia registro com SELECT FOR UPDATE, verifica revisão e só confirma após commit. Inicialização concorrente é protegida por PK e CHECK; violação de unicidade é tratada como conflito recuperável.
5. `AdminClinicConfigurationState` carrega e edita dois campos, preserva o formulário se a gravação falhar, diferencia erros por campo, conflito e sessão expirada. `PatientPortalState` lê o mesmo serviço dentro da transação autenticada da agenda.
6. Reutilizar `section_panel`, `field_label`, `feedback_region` e estilos `vitta-*`. Manter a marca Vitta One inalterada.

## Riscos e rollback

A migration requer PostgreSQL QA isolado antes do merge. Alteração simultânea da primeira configuração pode retornar conflito, mas nunca cria múltiplas configurações. Downgrade da migration remove dados e auditoria; somente em QA descartável.

## Validação

Testar RBAC, sessão inválida, strings vazias/somente espaços, limites, leitura após nova sessão, idempotência, conflito de revisão, auditoria e fallback. Executar Pytest, OpenSpec strict, Reflex compile e Chromium/teclado/responsividade no ambiente CI/QA.
