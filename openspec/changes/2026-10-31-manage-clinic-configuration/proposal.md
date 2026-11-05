## Por que

A página `/admin/configuracoes` informa o endereço por variáveis de ambiente, sem formulário. A equipe depende de implantação para editar dados institucionais que precisam aparecer no portal do paciente.

## O que muda

- Criar edição restrita ao Administrador para nome e endereço da clínica.
- Persistir os dados no PostgreSQL em registro único com revisão e trilha de auditoria.
- Priorizar os dados persistidos e usar variáveis de ambiente apenas como fallback antes da primeira configuração salva.
- Mostrar configuração, validação e feedback acessíveis; impedir escrita com sessão inválida ou perfil não autorizado.
- Atualizar as leituras do portal sem restart, mantendo a marca Vitta One.

## Capabilities

- ADDED: clinic-settings
- MODIFIED: patient-portal

## Fora do escopo

Multiclínica, mudança da marca, credenciais/segredos em UI, configurações financeiras, endpoints REST independentes, deploy e alteração de `.env` via interface.
