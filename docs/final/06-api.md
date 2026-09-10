# 06 — API

## Convenções gerais

- Todos os endpoints de negócio têm prefixo `/api`. Além destes, a aplicação expõe `GET /health`
  (fora do prefixo, checagem simples de que o processo subiu) e as rotas de página HTML
  (`/`, `/login`, `/customers`, `/accounts`, `/accounts/{id}`, `/pix/transfer` — ver `08-frontend.md`).
- Todo valor monetário é inteiro em **centavos** (`*_cents`), nunca `float`.
- Todo schema de entrada (`*Create`, `*Update`, `LoginRequest`, `DepositRequest` etc.) usa
  `model_config = ConfigDict(extra="forbid")` — qualquer campo não declarado no schema é rejeitado
  com `422`, não apenas ignorado. É esse mecanismo que impede, por exemplo, alterar `balance_cents`
  por um `PUT /api/accounts/{id}` (o schema `AccountUpdate` só tem `agency` e `label`).
- Autenticação por **sessão via cookie assinado** (`SessionMiddleware`, `itsdangerous`). O frontend
  não anexa nenhum header manualmente — o cookie é enviado automaticamente pelo navegador em cada
  `fetch()` no mesmo domínio.

## Códigos HTTP e como são gerados

| Código | Quando |
|---|---|
| `200 OK` | leitura ou atualização bem-sucedida |
| `201 Created` | criação bem-sucedida |
| `204 No Content` | remoção bem-sucedida, logout |
| `400 Bad Request` | regra de negócio violada (saldo insuficiente, valor inválido, transferência para si mesmo, forma de transação inválida) |
| `401 Unauthorized` | sem sessão de login válida, ou credenciais inválidas no login |
| `403 Forbidden` | autenticado, mas sem permissão para a operação |
| `404 Not Found` | recurso não encontrado |
| `409 Conflict` | conflito de unicidade, ou dependência que impede exclusão |
| `422 Unprocessable Entity` | corpo inválido — schema Pydantic (tipo errado, campo faltando ou não permitido) **ou** CPF/chave Pix com formato inválido |

**Como o código HTTP é decidido, na implementação real:** `app/adapters/inbound/api/exception_handlers.py`
define um dicionário `_STATUS_BY_EXCEPTION: dict[type[Exception], int]` que associa cada exceção
concreta de domínio (ver lista completa em `04-modelo-de-dominio.md`) a um código HTTP, e registra
um handler individual por tipo via `app.add_exception_handler(...)`. São **N handlers específicos,
um por subclasse**, em vez de um único handler genérico na classe-base. Cada exceção de domínio não
tratada localmente vira uma resposta `{"detail": "..."}` com o código certo, então nenhum
Controller precisa de `try/except` repetido.

## Autenticação (`/api/auth`)

Implementado em `app/adapters/inbound/api/auth_controller.py`.

### `POST /api/auth/login`
Autentica via `CustomerService.authenticate(email, password)` e grava `customer_id` na sessão.

Request:
```json
{ "email": "maria@example.com", "password": "senha-da-maria" }
```
Response `200`:
```json
{ "id": 2, "name": "Maria Silva", "email": "maria@example.com", "role": "CUSTOMER" }
```
Erro: `401` se email não existe ou senha não confere (`InvalidCredentialsError`).

### `POST /api/auth/logout`
Limpa `request.session`. Response `204`, sem corpo.

### `GET /api/auth/me`
Retorna o cliente da sessão atual (via `get_current_customer`, ver `03-arquitetura.md`). Erro: `401`
se não há sessão (`NotAuthenticatedError`).

## Matriz de autorização

Checada nos Controllers (`ensure_admin` / `ensure_self_or_admin` / `ensure_account_owner_or_admin`
em `app/adapters/inbound/api/authorization.py`) — **nunca** dentro dos Services.

| Endpoint | Quem pode |
|---|---|
| `POST` / `GET /api/customers` | ADMIN |
| `GET` / `PUT /api/customers/{id}` | ADMIN ou o próprio cliente |
| `DELETE /api/customers/{id}` | ADMIN |
| `GET /api/customers/{id}/accounts` | ADMIN ou o próprio cliente |
| `POST` / `PUT` / `DELETE /api/accounts` | ADMIN |
| `GET /api/accounts` | ADMIN vê todas; cliente vê só as próprias (filtrado no Controller, não é 403) |
| `GET /api/accounts/{id}`, `/balance`, `/transactions`, `/pix-keys` | ADMIN ou dono da conta |
| `POST /api/accounts/{id}/deposit`, `/withdraw` | ADMIN ou dono da conta |
| `POST /api/pix-keys` | ADMIN ou dono da conta informada no corpo |
| `GET /api/pix-keys` (todas) | ADMIN |
| `GET`/`PUT`/`DELETE /api/pix-keys/{id}` | ADMIN ou dono da conta da chave |
| `POST /api/pix/transfers` | ADMIN ou dono da conta de origem |

## Customers (`/api/customers`)

Implementado em `customer_controller.py`, sobre `CustomerService`.

### `POST /api/customers` — cria um cliente (ADMIN)
```json
// request (CustomerCreate)
{ "name": "Maria Silva", "email": "maria@example.com", "cpf": "52998224725",
  "password": "senha-da-maria", "role": "CUSTOMER" }
```
```json
// response 201 (CustomerRead) — password_hash nunca é exposto
{ "id": 2, "name": "Maria Silva", "email": "maria@example.com", "cpf": "52998224725",
  "role": "CUSTOMER", "created_at": "2026-09-09T12:00:00Z" }
```
Erros: `422` (CPF inválido), `409` (email ou CPF já cadastrado).

### `GET /api/customers` — lista todos (ADMIN)
Response `200`: array de `CustomerRead`.

### `GET /api/customers/{id}` — consulta (ADMIN ou o próprio)
Response `200`: `CustomerRead`. Erro `404`.

### `PUT /api/customers/{id}` — atualiza `name`/`email` (ADMIN ou o próprio)
`cpf` não está no schema `CustomerUpdate` — não é editável por esta rota. Erros: `404`, `409`.

### `DELETE /api/customers/{id}` — remove (ADMIN)
`204`. Erro `409` se o cliente tiver contas (`CustomerHasAccountsError`).

### `GET /api/customers/{id}/accounts` — contas de um cliente (ADMIN ou o próprio)
Response `200`: array de `AccountRead`. Implementado com o mesmo `AccountService` do
`account_controller.py` — `customer_controller.py` importa `get_account_service` de lá para não
duplicar a função de *wiring*.

## Accounts (`/api/accounts`)

Implementado em `account_controller.py`, sobre `AccountService`.

### `POST /api/accounts` — cria conta vinculada a um cliente (ADMIN)
```json
{ "customer_id": 2, "agency": "0001", "number": "123456", "label": "Conta principal" }
```
`201` com `balance_cents: 0`. Erros: `404` (cliente inexistente), `409` (`number` já em uso).

### `GET /api/accounts` — lista (ADMIN vê todas; cliente vê só as próprias)
Filtragem acontece dentro do handler: `service.list() if current.role == "ADMIN" else
service.list_by_customer(current.id)`.

### `GET /api/accounts/{id}` — consulta (ADMIN ou dono)
`200`. Erro `404`.

### `PUT /api/accounts/{id}` — atualiza `agency`/`label` (ADMIN)
`balance_cents`, `number` e `customer_id` **não existem** no schema `AccountUpdate` — enviá-los é
rejeitado com `422`, não apenas ignorado.

### `DELETE /api/accounts/{id}` — remove (ADMIN)
`204`. Erro `409` (`AccountHasDependenciesError` — saldo, chaves Pix ou transações).

### `GET /api/accounts/{id}/balance`
```json
{ "account_id": 10, "balance_cents": 1050 }
```

### `POST /api/accounts/{id}/deposit` (ADMIN ou dono)
```json
// request (DepositRequest)
{ "amount_cents": 1050 }
```
```json
// response 201 (TransactionRead)
{ "id": 100, "source_account_id": null, "destination_account_id": 10,
  "type": "DEPOSIT", "amount_cents": 1050, "description": null,
  "created_at": "2026-09-09T12:10:00Z" }
```
Erros: `404`; `400` se `amount_cents <= 0`.

### `POST /api/accounts/{id}/withdraw` (ADMIN ou dono)
Mesmo formato, `type: "WITHDRAW"`, `source_account_id` preenchido, `destination_account_id: null`.
Erros: `404`; `400` (valor inválido ou saldo insuficiente).

### `GET /api/accounts/{id}/transactions` — extrato (ADMIN ou dono)
`200`: array de `TransactionRead`, mais recente primeiro (`ORDER BY created_at DESC`, feito no
Repository Adapter). Erro `404`.

### `GET /api/accounts/{id}/pix-keys` (ADMIN ou dono)
`200`: array de `PixKeyRead` daquela conta. Erro `404`.

## Pix Keys (`/api/pix-keys`)

Implementado em `pix_key_controller.py`, sobre `PixKeyService`.

### `POST /api/pix-keys` (ADMIN ou dono da conta informada)
```json
{ "account_id": 10, "type": "EMAIL", "value": "maria@example.com" }
```
`201`. Erros: `404` (conta inexistente); `422` (formato inválido para o tipo); `409` (valor já
cadastrado).

### `GET /api/pix-keys` — todas (ADMIN)

### `GET /api/pix-keys/{id}` (ADMIN ou dono da conta da chave)
Erro `404`.

### `PUT /api/pix-keys/{id}` (ADMIN ou dono)
`account_id` não está em `PixKeyUpdate` — não editável. Revalida formato/unicidade do novo valor.
Erros: `404`; `422`; `409`.

### `DELETE /api/pix-keys/{id}` (ADMIN ou dono)
`204`. Sem restrição de dependentes — sempre permitido se a chave existir. Erro `404`.

## Pix Transfer (`/api/pix`)

Implementado em `pix_transfer_controller.py`, sobre `PixTransferService`.

### `POST /api/pix/transfers` (ADMIN ou dono da conta de origem)
```json
{ "source_account_id": 10, "pix_key_value": "joao@example.com", "amount_cents": 2000 }
```
```json
// response 201
{ "id": 101, "source_account_id": 10, "destination_account_id": 11,
  "type": "PIX_TRANSFER", "amount_cents": 2000, "description": null,
  "created_at": "2026-09-09T12:20:00Z" }
```
Erros:
- `404` — conta de origem não encontrada, **ou** chave Pix não encontrada.
- `400` — valor `<= 0`, mesma conta, ou saldo insuficiente na origem.

Ver `07-fluxos-principais.md` para o passo a passo interno completo desta rota — é o fluxo mais
elaborado do sistema.

## Resumo de rotas (backend real)

```
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me

POST   /api/customers
GET    /api/customers
GET    /api/customers/{id}
PUT    /api/customers/{id}
DELETE /api/customers/{id}
GET    /api/customers/{id}/accounts

POST   /api/accounts
GET    /api/accounts
GET    /api/accounts/{id}
PUT    /api/accounts/{id}
DELETE /api/accounts/{id}
GET    /api/accounts/{id}/balance
POST   /api/accounts/{id}/deposit
POST   /api/accounts/{id}/withdraw
GET    /api/accounts/{id}/transactions
GET    /api/accounts/{id}/pix-keys

POST   /api/pix-keys
GET    /api/pix-keys
GET    /api/pix-keys/{id}
PUT    /api/pix-keys/{id}
DELETE /api/pix-keys/{id}

POST   /api/pix/transfers

GET    /health
```

Documentação interativa gerada automaticamente pelo próprio FastAPI (Swagger UI) em `/docs` quando
a aplicação está rodando — este documento não repete o schema OpenAPI campo a campo; foca em
explicar o *porquê* de cada decisão de design da API (validação estrita de schema, autorização no
Controller, mapeamento de exceção para status HTTP).
