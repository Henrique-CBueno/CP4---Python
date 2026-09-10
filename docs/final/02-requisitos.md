# 02 — Requisitos

## Requisitos acadêmicos obrigatórios (enunciado do trabalho)

Estes são os requisitos mínimos exigidos pelo enunciado do trabalho:

1. Utilizar **FastAPI** para desenvolver a API.
2. Utilizar **SQLite** como banco de dados.
3. Separar o backend, no mínimo, entre **Controller** (rotas) e **Service** (regras de negócio).
4. Possuir **pelo menos dois modelos relacionados**.
5. Implementar operações de **criação, consulta, atualização e remoção (CRUD)**.
6. Criar uma **interface web** utilizando HTML e CSS.
7. O **frontend deve consumir os endpoints da API** (via `fetch()`).
8. Os dados devem ser **persistidos em SQLite**.

## Requisitos funcionais implementados

### Autenticação e autorização

| ID | Requisito |
|---|---|
| RF00a | Login por email/senha, com sessão via cookie assinado |
| RF00b | Logout |
| RF00c | Cada `Customer` tem um papel (`role`): `ADMIN` ou `CUSTOMER` |
| RF00d | Um cliente logado só vê/opera as próprias contas; um admin vê e opera qualquer conta e cliente |

### Clientes (Customer)

| ID | Requisito |
|---|---|
| RF01 | Cadastrar cliente (nome, email, CPF, senha) — operação de admin |
| RF02 | Listar clientes — admin |
| RF03 | Consultar cliente por id — admin ou o próprio cliente |
| RF04 | Atualizar nome/email de um cliente — admin ou o próprio cliente |
| RF05 | Remover cliente (bloqueado se houver contas associadas) — admin |
| RF06 | Listar contas de um cliente — admin ou o próprio cliente |

### Contas (Account)

| ID | Requisito |
|---|---|
| RF07 | Criar conta vinculada a um cliente |
| RF08 | Listar contas (admin vê todas; cliente vê só as próprias) |
| RF09 | Consultar conta por id |
| RF10 | Atualizar `agency`/`label` de uma conta |
| RF11 | Remover conta (bloqueado se houver saldo, chaves Pix ou transações associadas) |
| RF12 | Consultar saldo de uma conta |
| RF13 | Depositar em uma conta |
| RF14 | Sacar de uma conta |

### Chaves Pix (PixKey)

| ID | Requisito |
|---|---|
| RF15 | Cadastrar chave Pix vinculada a uma conta (`CPF`, `EMAIL`, `PHONE` ou `RANDOM`) |
| RF16 | Listar todas as chaves Pix — admin |
| RF17 | Listar chaves Pix de uma conta específica |
| RF18 | Consultar chave Pix por id |
| RF19 | Atualizar chave Pix (tipo e/ou valor, com revalidação) |
| RF20 | Remover chave Pix |

### Transferência Pix e extrato

| ID | Requisito |
|---|---|
| RF21 | Transferir valor entre contas via chave Pix, com validação completa (saldo, chave existente, não transferir para si mesmo) |
| RF22 | Listar transações (extrato) de uma conta, identificando tipo e direção |

## Requisitos não funcionais

| ID | Requisito | Onde é cumprido |
|---|---|---|
| RNF01 | Código organizado em camadas, com Controller e Service claramente distintos | `app/adapters/inbound/api/` vs `app/application/services/` (ver `03-arquitetura.md`) |
| RNF02 | Toda representação monetária usa inteiros em centavos (nunca `float`) | `Account.balance_cents`, `Transaction.amount_cents` (ver `04-modelo-de-dominio.md`) |
| RNF03 | Executável localmente sem infraestrutura externa | `uvicorn` + arquivo `bank.db`, sem rede/containers |
| RNF04 | Regras de negócio cobertas por testes automatizados | `tests/unit/`, `tests/service/`, `tests/api/` (ver `09-testes.md`) |
| RNF05 | Operações financeiras são atômicas | uma única `Session` de SQLAlchemy por requisição, commit único no fim (ver `07-fluxos-principais.md`) |
| RNF06 | API documentada automaticamente via OpenAPI/Swagger | gerado pelo próprio FastAPI em `/docs` |

## Matriz de rastreabilidade — requisito do enunciado → implementação

| Requisito do enunciado | Onde é atendido |
|---|---|
| Utilizar FastAPI | `app/main.py` cria a aplicação `FastAPI(...)`; rotas em `app/adapters/inbound/api/*_controller.py` |
| Utilizar SQLite | `app/infrastructure/db.py` (`create_engine(DATABASE_URL)`), arquivo `bank.db` na raiz do projeto |
| Separar Controller e Service | Controllers em `app/adapters/inbound/api/`; Services em `app/application/services/` — nenhum controller contém regra de negócio |
| Pelo menos 2 modelos relacionados | `Customer 1—N Account`, `Account 1—N PixKey`, `Account 1—N Transaction` (origem e destino) — ver `04-modelo-de-dominio.md` |
| CRUD completo | `Customer`, `Account` e `PixKey` têm criar/listar/consultar/atualizar/remover (ver `06-api.md`) |
| Interface web HTML/CSS | `app/templates/*.html` (Jinja2) + `app/static/css/style.css` |
| Frontend consome a API via `fetch()` | `app/static/js/*.js` — nenhuma página faz `<form action="...">` tradicional; toda interação passa por `apiGet`/`apiPost`/`apiPut`/`apiDelete` em `api.js` |
| Dados persistidos em SQLite | Modelos SQLAlchemy em `app/adapters/outbound/persistence/models.py`, persistidos em `bank.db` |

## Funcionalidades extras (além do mínimo exigido)

O enunciado não exige autenticação, controle de papéis, migrações versionadas ou testes
automatizados de ponta a ponta pela interface — mas o projeto inclui esses itens para reforçar a
demonstração de boas práticas. É importante distinguir claramente o que é exigência mínima do que é
acréscimo deliberado:

| Extra implementado | Por que foi adicionado |
|---|---|
| **Login por sessão + papéis `ADMIN`/`CUSTOMER`** | Sem isso, qualquer cliente poderia operar a conta de qualquer outro — a autorização dá sentido real às regras de negócio (ex.: "não é permitido transferir para a própria conta" só é interessante se também existir "não é permitido mexer na conta de outra pessoa") |
| **Matriz de autorização por endpoint** (`authorization.py`: `ensure_admin`, `ensure_self_or_admin`, `ensure_account_owner_or_admin`) | Torna a separação Controller/Service mais didática: a autorização fica no Controller, a regra de negócio fica no Service |
| **Alembic (migrações versionadas)**, além do `create_all()` simples | Demonstra o caminho "correto" de evolução de schema em um projeto real, sem abandonar o atalho rápido (`scripts/init_db.py`) usado pelos testes |
| **Suíte de testes em 3 camadas** (unit / service / API), não só testes de API | Torna visível que as regras de negócio são testadas isoladamente do banco e do HTTP, não só via `TestClient` |
| **`scripts/e2e_demo.py`** (Playwright) | Demonstração automatizada, pela interface web real (não pela API direto), da jornada completa de um usuário — útil para a apresentação oral, não é parte da suíte `pytest` |
| **`GET /health`** | Endpoint simples de verificação de que o processo subiu, comum em APIs reais |

## Fora do escopo (deliberadamente não implementado)

- OAuth, JWT em header, verificação de email, "esqueci minha senha".
- CSRF, rate limiting e demais *hardenings* de autenticação de nível produção.
- Integração real com o Banco Central, sistema Pix real ou QR Code Pix real.
- Gateways de pagamento (Stripe, Mercado Pago etc.).
- Event sourcing, CQRS, filas de mensageria, background workers.
- Microserviços e transações distribuídas.
- Docker obrigatório e deployment em nuvem.
- Frameworks de injeção de dependência (usa-se só `Depends()` nativo do FastAPI).

Justificativa de cada exclusão em `10-decisoes-tecnicas.md`.

## Critérios de aceite

1. Todos os CRUDs (`Customer`, `Account`, `PixKey`) funcionam de ponta a ponta pela interface web,
   não apenas pelo Swagger.
2. Depósito, saque e transferência Pix aplicam corretamente as regras de negócio: saldo nunca fica
   negativo, valores devem ser positivos, chave Pix deve existir, não é permitido transferir para a
   própria conta.
3. O extrato de uma conta reflete corretamente depósitos, saques e transferências (como origem e
   como destino).
4. Uma transferência Pix nunca deixa o sistema em estado inconsistente — ou debita, credita e
   registra tudo, ou nada é alterado (ver `07-fluxos-principais.md`, seção de atomicidade).
5. A suíte `pytest` cobre os cenários felizes e de erro listados em `09-testes.md` e passa sem
   falhas.
6. `README.md` (raiz do projeto) explica como instalar dependências, inicializar o banco e rodar a
   aplicação localmente.

Todos os seis critérios acima são verificáveis diretamente no código deste repositório, sem
depender de infraestrutura externa.
