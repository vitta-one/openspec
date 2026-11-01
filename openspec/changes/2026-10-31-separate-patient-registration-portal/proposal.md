# Separar edição cadastral e acesso ao portal na ficha do paciente

## Problema

A Recepção reúne dados cadastrais, acesso ao portal e atalho de agendamento em uma única superfície de gerenciamento. A edição acopla os inputs diretamente à projeção da ficha, permitindo que ela pareça atualizada antes da persistência.

## Objetivo

Disponibilizar dois modais independentes na ficha do paciente: **Editar cadastro** e **Acesso ao portal**, com validação/autorização no servidor, estados reais de convite e feedback acessível.

## Escopo

- Substituir a ação agrupada por duas ações distintas na ficha.
- Isolar rascunhos de nome e telefone e persistir somente após validação.
- Reutilizar State, serviços de paciente, convite e autenticação.
- Consultar status do portal a cada abertura e apresentar e-mail associado quando houver.
- Exigir consentimento em cada convite, evitar duplicidade e limitar reenvio.
- Manter compatibilidade com link antigo `/editar` sem formulário duplicado.
- Preservar agendamento como ação própria da ficha.

## Fora do escopo

- Edição de CPF, redefinição de vínculo de conta, alteração de credenciais.
- Criar serviço de e-mail ou autenticação paralelo.
- Envio em produção, migração destrutiva, alteração no fluxo clínico.
- Remover as ferramentas locais de QA do projeto.

## Riscos

- Falha do provedor não equivale a entrega ao destinatário.
- O rate limit por paciente em banco não substitui proteção global de abuso.
- Testes manuais de teclado, foco e responsividade dependem de navegador configurado.
