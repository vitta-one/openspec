# Change: Cadastro seguro e acessível de novos pacientes na Recepção

## Por quê

O formulário dedicado de cadastro ocupa largura excessiva, exige pontuação manual no CPF, oferece feedback genérico e dificulta a recuperação de erros. O modelo atual já contém CPF único e o serviço de domínio já valida o CPF; a mudança aprimora a experiência sem criar um segundo cadastro ou alterar a arquitetura.

## O que muda

- Formulário compacto com dados pessoais em uma coluna e ações responsivas.
- Máscara progressiva de CPF e telefone opcional, aceitando digitação e colagem.
- Validação server-side dos campos e feedback inline associado aos controles.
- Tratamento explícito do CPF duplicado, com acesso à ficha somente sob autorização existente.
- Proteção contra reenvio e link recuperável quando a persistência acontece antes de uma falha de navegação.
- Navegação para a ficha individual imediatamente após confirmação da persistência.

## Fora de escopo

- Novas colunas, migrations ou modelos de paciente.
- Criar entradas na fila, consultas ou prontuários automaticamente.
- Cadastro paralelo dentro da Agenda.
- Alteração das regras de autorização, perfis ou rotas públicas.
- Mudanças no portal do paciente ou em integrações externas.

## Impacto

- UI: `vitta_one/ui/patient_directory_components.py`, `assets/styles.css`.
- State/roteamento: `vitta_one/patient_queue/state.py`, `vitta_one/vitta_one.py`.
- Domínio: validação de gramática de CPF em `vitta_one/patient_queue/service.py`.
- Testes: validação e máscaras; regressão do serviço de pacientes.
- Não há mudança em esquema de banco: `patients.cpf` já é `UNIQUE`.

## Riscos e verificação

- Eventos Reflex e formato das máscaras devem ser homologados em Chromium com teclado, colagem e dispositivos móveis.
- A restrição de CPF único deve ser exercitada em PostgreSQL de QA sob concorrência.
- Não usar dados reais de pacientes durante os testes.
