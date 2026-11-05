# Design — cadastro unificado da equipe

## Solução

A página canônica mantém apenas um formulário Reflex. `AdminStaffState` é responsável por identificação compartilhada, perfil escolhido, validação visível, confirmação de descarte e orquestração de persistência. As especialidades usam as opções já carregadas pelo `AdminDirectoryState` e o mesmo checkbox de `admin_directory_components.py`. Nome e e-mail não são apagados por alteração de perfil.

## Serviços

- Recepcionista: `create_receptionist` valida nome de 2–160 caracteres, e-mail único e senha; role é fixada no servidor e `IntegrityError` é tratado.
- Médico: `admin_register_medical_professional` reaproveita criação atômica de `User`, `Professional` e vínculos, autorização ADMINISTRADOR e senha temporária; uma coleção vazia de especialidades é válida.
- Resend: `send_medical_welcome` e `admin_set_onboarding_email_status` já existentes são usados sem criar credenciais paralelas. O sistema não afirma e-mail entregue quando houve somente aceite do provedor.
- Em cada mutação o serviço exige sessão/role. Dados de outros perfis não entram na chamada de persistência, mesmo se o cliente os enviar.
- A senha preenchida não é mantida em State; só o indicador booleano de edição é armazenado para solicitar confirmação de descarte.

## UI e acessibilidade

Container centralizado de 46rem, campos alinhados, um único rodapé de ações. Select Radix; labels visíveis; ajuda contextual; erros `aria-invalid`/`aria-describedby` e região de alerta. Senha com mostrar/ocultar e `aria-pressed`; especialidades com seleção por teclado, estado vazio e lista compacta. Diálogos de confirmação usam primitive Radix com foco controlado. Botões empilham no mobile e respeitam movimento reduzido.

## Falhas e idempotência

Cliente impede clique repetido enquanto `saving`; banco impede e-mail duplicado inclusive sob corrida. Criação médica e seus vínculos são transacionais. Se envio externo falhar após persistência, a conta continua criada, status é informado sem incentivar duplicação e o registro pode ser consultado. Falhas de autorização redirecionam sem expor cadastro.

## Migração

Não aplicável: reutiliza `auth_users.display_name` da PR #325 e as relações existentes.

## Verificação

Pytest (validação, perfis, duplicidade, especialidades vazias/múltiplas, autorização), OpenSpec strict, `reflex compile --dry`, Chromium com fluxo e viewports 320/390/768/1024/1440.
