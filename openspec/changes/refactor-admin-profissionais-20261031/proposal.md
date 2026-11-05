## Why

A página `/admin/profissionais` apresenta registros em cards extensos, mistura a situação operacional do médico com o estado do convite de acesso e executa mudança de situação sem confirmação. O fluxo de especialidades obrigatórias impede cadastrar o profissional antes de definir a área, embora a UI de administração deva permitir o vínculo posteriormente.

## What Changes

- Converter a listagem completa em tabela semântica compacta e lista operacional no mobile, preservando filtros, paginação e diálogos já existentes.
- Distinguir status profissional de situação de envio do e-mail, sem presumir entrega, e apresentar ações secundárias em menu contextual.
- Exigir confirmação para desativar ou reativar; rejeitar confirmação com situação obsoleta no servidor.
- Permitir zero ou mais especialidades no cadastro/edição, sem aceitar novos vínculos inativos ou criar identidades duplicadas.
- Adicionar cenários de teste para especialidade opcional, associação, identidade e concorrência da mudança de situação.

## Capabilities

### Modified Capabilities

- `professional-specialty-management`: cadastro com especialidades opcionais e diretório administrativo seguro, com estados reais.

### New Capabilities

Nenhuma.

## Out of Scope

- Alterar o vínculo da conta de login ou ativar/desativar usuário ao mudar status profissional.
- Mudar fluxos de consultas e agenda além das validações já existentes.
- Mudar modelo de dados/migrations, criar integração paralela de e-mail ou realizar deploy.
- Trocar o Reflex ou implementar paginação SQL prematuramente.

## Impact

- `vitta_one/professional_directory/{service,application,state}.py`
- `vitta_one/ui/admin_directory_components.py`
- Testes de diretório e primeiro acesso.
- Sem migration; saída do Resend continua dependendo de configuração real do ambiente.
