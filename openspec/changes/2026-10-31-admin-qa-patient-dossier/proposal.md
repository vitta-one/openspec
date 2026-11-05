# Reorganizar visualização QA de pacientes no Administrador

## Problema
A rota `/admin/pacientes` mistura diretório, seleção por checkbox e históricos em expansão, entregando dados desnecessários à listagem e dificultando a navegação.

## Proposta
Separar `/admin/pacientes` (busca e paginação somente de identificação mascarada) e `/admin/pacientes/[patient_id]` (ficha de um paciente). A ficha oferece históricos operacional e clínico como seções independentes, com leitura clínica sob demanda.

## Escopo
- Preservar Python/Reflex, contratos e componentes de UI compartilhados.
- Preservar `VITTA_ONE_LOCAL_ADMIN_PREVIEW` e autorização de Administrador no servidor.
- Reutilizar projeção existente de histórico clínico concluído e autorizada.
- Não adicionar mutações, migrações, endpoints REST, permissões clínicas de produção ou dados fictícios.

## Impacto
Módulos: `admin_preview`, auth/roteamento, `ui/admin_preview_components`, testes de autorização. Banco: sem alteração.
