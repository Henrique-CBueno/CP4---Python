# 12 — Guia de Apresentação Oral

Roteiro para uma apresentação de **7 a 10 minutos**. Cada seção indica o que dizer, qual arquivo
abrir na tela, e quanto tempo gastar. O objetivo não é ler slides — é navegar pelo código real
enquanto fala.

## Roteiro (≈ 8 minutos)

### 1. Abertura (30s)
"Este projeto é uma simulação acadêmica de um banco digital — cadastro de clientes, contas, chaves
Pix, depósito, saque, transferência e extrato — construída com FastAPI, SQLAlchemy e SQLite, com uma
interface web em HTML/CSS/JavaScript que consome a própria API. Não é um banco real: não há
integração com o Banco Central nem com o sistema Pix verdadeiro."

**Não precisa abrir nada ainda.**

### 2. Problema e objetivo (30s)
"O objetivo não era construir o sistema bancário mais completo possível, e sim demonstrar, de forma
correta, a integração entre frontend, API, regras de negócio e banco de dados — com Controller e
Service claramente separados, que é o requisito central do trabalho."

**Abrir:** `docs/final/01-visao-geral.md` (mostrar rapidamente o diagrama de fluxo geral).

### 3. Arquitetura (90s)
"O backend segue uma arquitetura hexagonal simplificada: Controller → Service → Domínio → Port →
Adapter → SQLAlchemy → SQLite. Controller cuida de HTTP e autorização; Service cuida da regra de
negócio; Domínio tem as entidades; Port é uma interface de repositório; Adapter é quem realmente fala
com o SQLAlchemy."

**Abrir, nesta ordem:**
1. `app/adapters/inbound/api/account_controller.py` — mostrar que o handler só chama `service.xxx()`.
2. `app/application/services/account_service.py` — mostrar a regra de negócio de verdade.
3. `app/application/ports/account_repository.py` — mostrar o `Protocol`.
4. `app/adapters/outbound/persistence/account_repository_sqlalchemy.py` — mostrar a implementação
   concreta.

"Duas simplificações conscientes, documentadas em `docs/final/03-arquitetura.md`: `Transaction` não
tem entidade de domínio própria, por ser um registro que nunca muda depois de criado; e a checagem
de 'esse cliente é dono desta conta?' lê o repositório direto em alguns pontos, antes de chamar o
Service — pragmatismo assumido, não descuido."

### 4. Modelo de domínio (60s)
"Quatro conceitos: `Customer`, `Account`, `PixKey` e `Transaction`. Nenhuma entidade tem
comportamento próprio — `Account`, em particular, não guarda saldo como estado: o saldo é sempre
calculado somando as `Transaction` da conta (event sourcing). Valor positivo e saldo suficiente são
validados em `app/domain/balance_rules.py`, não em métodos da entidade."

**Abrir:** `app/domain/balance_rules.py` (curto, `validate_deposit`/`validate_withdraw`) e
`app/adapters/outbound/persistence/account_repository_sqlalchemy.py::_compute_balance()` (mostrar
de onde o saldo realmente vem).

### 5. Banco de dados (45s)
"Dinheiro é sempre inteiro em centavos, nunca `float` — evita erro de arredondamento. Quatro
tabelas — e `accounts` não tem coluna de saldo: `transactions` é a única fonte de verdade sobre
movimentações financeiras, o saldo é projetado a partir dela em tempo de leitura."

**Abrir:** `app/adapters/outbound/persistence/models.py` (mostrar que `Account` não tem
`balance_cents`) e a migration `alembic/versions/0f4be3daa031_remove_balance_cents_from_accounts.py`.

### 6. Frontend consumindo a API (45s)
"Nenhuma página tem `<form action>` tradicional — todo envio de dado passa por `fetch()`, através de
um helper único, `api.js`. `formatCents()` ali é a única conversão de centavos para reais do projeto
inteiro."

**Abrir:** `app/static/js/api.js` (é curto, mostrar `apiRequest` e `formatCents`).

### 7. Transferência Pix, passo a passo (90s) — o momento mais importante
"Este é o fluxo mais elaborado. Vale mostrar ao vivo porque combina domínio, atomicidade e
persistência."

**Abrir:** `app/application/services/pix_transfer_service.py`, e narrar linha por linha:
"Valida o valor primeiro. Busca a conta de origem. Resolve a chave Pix. Busca a conta de destino.
Rejeita se for a mesma conta. Valida o saldo — `balance_rules.validate_withdraw()`, contra o saldo
já calculado da conta de origem, é onde saldo insuficiente é detectado, antes de qualquer escrita.
Persiste a `Transaction` — esse é o único `INSERT`/`UPDATE` do fluxo inteiro, nenhuma conta é
mutada. Usa `flush()`, não `commit()` — o commit só acontece uma vez, depois que o Controller
retorna sem erro, lá em `get_db()`. Se qualquer coisa falhar antes desse `INSERT`, nada foi escrito
ainda."

**Se der tempo, mostrar também:**
`tests/service/test_pix_transfer_service.py::test_transfer_atomicity_on_failure` — o teste que força
uma falha na criação da `Transaction` e confirma, consultando o banco, que o saldo calculado não
mudou.

### 8. Testes (45s)
"A suíte tem três camadas: testes de domínio puro, sem banco; testes de serviço, com SQLite
temporário real; e testes de API, com `TestClient`, cobrindo os códigos HTTP documentados."

**Abrir:** `docs/final/09-testes.md` (mostrar a tabela requisito → teste).

### 9. Decisões técnicas (30s)
"Cada escolha tem uma alternativa que foi considerada e descartada por um motivo concreto — sem
JWT porque sessão simples já resolve o problema real (distinguir 'minha conta' de 'conta de
outro'); sem CQRS/Event Sourcing/microserviços porque o projeto não tem o problema que essas técnicas
resolvem."

**Abrir:** `docs/final/10-decisoes-tecnicas.md` (mencionar 1–2 decisões, não ler todas).

### 10. Encerramento (20s)
"Em resumo: separação real entre Controller e Service, regras de negócio testadas em três níveis,
persistência isolada atrás de interfaces, e duas simplificações conscientes e documentadas em vez de
escondidas. Fico à disposição para perguntas."

## Checklist de arquivos para ter abertos (em abas, prontos)

1. `docs/final/01-visao-geral.md`
2. `app/adapters/inbound/api/account_controller.py`
3. `app/application/services/account_service.py`
4. `app/application/ports/account_repository.py`
5. `app/adapters/outbound/persistence/account_repository_sqlalchemy.py`
6. `app/domain/entities/account.py`
7. `app/adapters/outbound/persistence/models.py`
8. `app/static/js/api.js`
9. `app/application/services/pix_transfer_service.py`
10. `tests/service/test_pix_transfer_service.py`
11. `docs/final/09-testes.md`
12. `docs/final/10-decisoes-tecnicas.md`

Opcional, se a apresentação for em ambiente com navegador disponível: rodar `python -m app.main` e
mostrar a aplicação funcionando ao vivo em `http://127.0.0.1:8000/`, ou rodar
`python -m scripts.e2e_demo --headed` para uma demonstração automatizada pela interface.

## Perguntas prováveis do professor e respostas curtas

**Por que FastAPI?**
"Exigência do enunciado; além disso gera OpenAPI/Swagger automaticamente a partir dos schemas
Pydantic e já tem injeção de dependência nativa via `Depends()`, suficiente para este projeto sem
precisar de um framework de DI separado."

**Por que SQLite?**
"Exigência do enunciado; roda sem servidor de banco separado, sem Docker, sem configuração de rede —
`git clone` e `pip install` bastam para rodar o projeto em qualquer máquina."

**Por que guardar dinheiro em centavos?**
"`float` tem erro de arredondamento binário — `0.1 + 0.2` não é exatamente `0.3`. Inteiro em
centavos resolve isso com o tipo mais simples possível, sem precisar de `Decimal` nem de um tipo
customizado no banco."

**Por que Controller e Service separados?**
"Era o requisito central do enunciado. Na prática, o Controller nunca decide se uma operação pode
ou não acontecer — quem decide é o Service (ou o Domínio, para regras como saldo insuficiente). Isso
significa que a mesma regra de negócio poderia ser testada sem depender de HTTP nenhum — é
exatamente o que os testes em `tests/service/` fazem."

**O que torna esta arquitetura "hexagonal"?**
"O Service não conhece SQLAlchemy — ele depende só de uma interface (`Protocol`), o Repository Port.
Quem implementa essa interface com SQLAlchemy é uma classe separada, o Repository Adapter. Isso
significa que, em teoria, dá para trocar SQLite por outro mecanismo de persistência sem tocar no
Service — e dá para testar o Service com um repositório falso, como o teste de atomicidade faz."

**Por que interfaces de repositório (Ports)?**
"Para inverter a dependência: o Service depende de uma abstração que ele mesmo define (o que
precisa), não da implementação concreta. Usamos `Protocol` em vez de classe abstrata porque o
contrato é verificado estruturalmente, sem exigir herança — reduz acoplamento entre a porta e quem a
implementa."

**Como a transferência Pix se mantém consistente?**
"Toda a operação — buscar as duas contas, debitar, creditar, criar a `Transaction` — acontece dentro
de uma única `Session` do SQLAlchemy, usando `flush()` em vez de `commit()`. O commit só acontece uma
vez, no fim da requisição, depois que tudo deu certo. Se qualquer passo falhar no meio, a exceção
propaga, o commit nunca acontece, e a sessão é descartada sem confirmar nada — é o mesmo que um
rollback. Tem um teste que força exatamente essa falha e confirma que nenhuma conta ficou com saldo
alterado."

**Por que não uma integração Pix real?**
"Integração real exigiria credenciamento junto ao Banco Central, certificados e ambiente de
homologação — fora do alcance de um trabalho acadêmico. O valor didático está em modelar
corretamente a forma da transferência (chave → conta de destino, débito e crédito atômicos), não em
processá-la de verdade."

**Por que SQLAlchemy síncrono, não assíncrono?**
"FastAPI já roda rotas síncronas em threadpool automaticamente, então não haveria ganho de
performance perceptível para este volume — e o SQLite, de qualquer forma, só permite um *writer* por
vez. Síncrono é mais direto de ler e depurar, sem `await` espalhado por todas as camadas."

**Por que `Transaction` tem `source_account_id` e `destination_account_id` em vez de duas tabelas
separadas (uma de depósitos/saques e outra de transferências)?**
"É a forma padrão de modelar um ledger simples: uma tabela única, duas colunas opcionais. `DEPOSIT`
só preenche o destino, `WITHDRAW` só preenche a origem, `PIX_TRANSFER` preenche os dois. Isso evita
ter que fazer `UNION` entre tabelas para montar um extrato — o extrato de uma conta é uma única
consulta, `WHERE source_account_id = :id OR destination_account_id = :id`."
