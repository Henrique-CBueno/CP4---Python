# 04 — Modelo de Domínio

## Visão geral

O domínio tem 4 conceitos: `Customer`, `Account`, `PixKey` e `Transaction`. Todos são **entidades
de domínio puras** — `dataclass` do Python, em `app/domain/entities/`, sem nenhuma dependência de
SQLAlchemy ou de qualquer outra camada.

| Conceito | É entidade de domínio pura? | Onde vive |
|---|---|---|
| `Customer` | Sim | `app/domain/entities/customer.py` |
| `Account` | Sim (com comportamento: `deposit()`, `withdraw()`) | `app/domain/entities/account.py` |
| `PixKey` | Sim | `app/domain/entities/pix_key.py` |
| `Transaction` | Sim | `app/domain/entities/transaction.py` |

## `Customer`

**Responsabilidade:** representar uma pessoa cadastrada no banco simulado — cliente comum ou
administrador. É o único conceito de domínio que também carrega autenticação (hash de senha, papel).

```python
@dataclass
class Customer:
    id: int | None
    name: str
    email: str
    cpf: str
    password_hash: str
    role: str = "CUSTOMER"
    created_at: datetime | None = None
```

| Campo | Regra |
|---|---|
| `email` | formato válido (`domain/validators.py::is_valid_email`); único no sistema |
| `cpf` | 11 dígitos com dígito verificador válido (`is_valid_cpf`); único no sistema; **imutável** após criação |
| `password_hash` | nunca é a senha em texto puro — gerado por `password_hashing.hash_password()` |
| `role` | `"ADMIN"` ou `"CUSTOMER"` |

**Relacionamentos:** um `Customer` possui zero ou mais `Account` (`Customer 1 — N Account`).

**Regras de negócio:** `Customer` em si é uma entidade sem métodos de comportamento (dataclass sem
lógica) — as regras que o envolvem (unicidade de email/CPF, bloqueio de exclusão com contas
associadas, autenticação) vivem em `CustomerService`, não na entidade. Isso é intencional: só
`Account` tem comportamento real o suficiente para justificar métodos na própria entidade (ver
seção `Account` abaixo).

**Exceções relacionadas:** `CustomerNotFoundError`, `DuplicateEmailError`, `DuplicateCpfError`,
`InvalidCpfError`, `CustomerHasAccountsError`, `InvalidCredentialsError`, `NotAuthenticatedError`.

## `Account`

**Responsabilidade:** representar uma conta bancária vinculada a um cliente, com saldo e as duas
únicas regras de negócio da aplicação que se expressam como métodos de comportamento no próprio
domínio.

```python
@dataclass
class Account:
    id: int | None
    customer_id: int
    agency: str
    number: str
    label: str | None = None
    balance_cents: int = 0
    created_at: datetime | None = None

    def deposit(self, amount_cents: int) -> None:
        if amount_cents <= 0:
            raise InvalidAmountError(amount_cents)
        self.balance_cents += amount_cents

    def withdraw(self, amount_cents: int) -> None:
        if amount_cents <= 0:
            raise InvalidAmountError(amount_cents)
        if amount_cents > self.balance_cents:
            raise InsufficientBalanceError(self.id, amount_cents, self.balance_cents)
        self.balance_cents -= amount_cents
```

| Campo | Regra |
|---|---|
| `customer_id` | referencia um `Customer` existente |
| `number` | único globalmente no sistema |
| `agency` | informativo, não entra em regra de unicidade |
| `label` | apelido opcional |
| `balance_cents` | inteiro, nunca negativo, inicia em `0` |

**Relacionamentos:** pertence a um `Customer`; possui zero ou mais `PixKey`; participa de zero ou
mais `Transaction`, tanto como origem quanto como destino.

**Business rules e invariantes (verificáveis diretamente no código):**

- **Valor inválido:** `deposit()` e `withdraw()` rejeitam `amount_cents <= 0` com
  `InvalidAmountError` — mesma regra nos dois métodos, sem exceção para valores negativos ou zero.
- **Saldo insuficiente:** `withdraw()` rejeita `amount_cents > balance_cents` com
  `InsufficientBalanceError`, antes de alterar o saldo — o saldo só é decrementado se a validação
  passar.
- **Saldo nunca negativo:** garantido em três camadas simultaneamente — pela lógica em `withdraw()`,
  por uma `CheckConstraint("balance_cents >= 0")` na tabela `accounts` (rede de segurança no banco),
  e por testes automatizados (`tests/unit/`, `tests/service/test_account_service.py`).
- **Exclusão bloqueada:** uma `Account` só pode ser removida se `balance_cents == 0` e não tiver
  `PixKey` nem `Transaction` associada — regra aplicada em `AccountService.delete()`, não na
  entidade.

**Exceções relacionadas:** `AccountNotFoundError`, `DuplicateAccountNumberError`,
`InvalidAmountError`, `InsufficientBalanceError`, `AccountHasDependenciesError`.

## `PixKey`

**Responsabilidade:** representar uma chave Pix simulada, vinculada a uma conta, usada para resolver
a conta de destino em uma transferência.

```python
@dataclass
class PixKey:
    id: int | None
    account_id: int
    type: str
    value: str
    created_at: datetime | None = None
```

| Campo | Regra |
|---|---|
| `account_id` | referencia uma `Account` existente |
| `type` | `"CPF"`, `"EMAIL"`, `"PHONE"` ou `"RANDOM"` |
| `value` | formato validado conforme `type` (`domain/validators.py::is_valid_pix_key`); único globalmente, independente do tipo |

**Ponto de atenção sobre o campo `type`:** na entidade de domínio, `type` é um `str` simples, **não**
um `Enum` do Python. A validação dos quatro valores permitidos acontece em duas camadas diferentes,
não na entidade em si:

- na borda da API, o schema Pydantic `PixKeyType(str, Enum)` (`adapters/inbound/api/schemas.py`)
  restringe o valor aceito no corpo da requisição, e o controller converte para `str` com
  `body.type.value` antes de repassar ao Service;
- no domínio, `validators.is_valid_pix_key(key_type, value)` decide qual validação de formato aplicar
  a partir da string recebida (`CPF` → `is_valid_cpf`, `EMAIL` → `is_valid_email`, etc.);
- no banco, uma `CheckConstraint("type IN ('CPF','EMAIL','PHONE','RANDOM')")` funciona como rede de
  segurança final.

Essa é uma diferença pequena, mas real, em relação a `docs/specs/02-domain-model.md`, que descreve
`type` como `PixKeyType (enum)` diretamente na entidade — na implementação, o enum existe só na
camada de API, o domínio trabalha com `str`.

**Relacionamentos:** pertence a uma `Account`.

**Business rules:**

- **Formato por tipo:** o valor precisa satisfazer o formato esperado do tipo declarado (CPF válido,
  email válido, telefone `+?\d{10,15}`, ou UUID para `RANDOM`) — validada tanto na criação quanto na
  atualização (`PixKeyService.create()` / `.update()`), sempre revalidando o tipo efetivo (novo, se
  informado; atual, caso contrário).
- **Unicidade global:** `value` é único no sistema inteiro, independentemente do `type` — duas contas
  não podem registrar a mesma chave, mesmo que de tipos diferentes.
- **Sem dependentes:** ao contrário de `Customer` e `Account`, `PixKey` não bloqueia exclusão de
  nada — pode ser removida livremente.

**Exceções relacionadas:** `PixKeyNotFoundError`, `InvalidPixKeyError`, `DuplicatePixKeyError`,
`AccountNotFoundError` (ao criar/listar chaves de uma conta inexistente).

## `Transaction` (persistência, sem entidade de domínio própria)

**Responsabilidade:** registrar, de forma imutável (*create-only*, nunca atualizada nem removida), o
histórico de movimentações financeiras — depósitos, saques e transferências Pix.

Modelada apenas como classe SQLAlchemy em `app/adapters/outbound/persistence/models.py`:

```python
class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int]
    source_account_id: Mapped[int | None]
    destination_account_id: Mapped[int | None]
    type: Mapped[str]            # "DEPOSIT" | "WITHDRAW" | "PIX_TRANSFER"
    amount_cents: Mapped[int]
    description: Mapped[str | None]
    created_at: Mapped[datetime]
```

Complementada pela validação pura em `app/domain/transaction_rules.py::validate_transaction_shape()`,
chamada pelo Service **antes** de qualquer inserção:

```python
_EXPECTED_SHAPE = {
    "DEPOSIT":      (False, True),   # (source obrigatório?, destination obrigatório?)
    "WITHDRAW":     (True, False),
    "PIX_TRANSFER": (True, True),
}
```

**Business rules e invariantes:**

- `amount_cents` é sempre positivo (`> 0`) — a direção do dinheiro vem do `type` e de qual campo está
  preenchido, nunca de um valor negativo.
- A forma de `source_account_id`/`destination_account_id` depende estritamente do `type`:

  | `type` | `source_account_id` | `destination_account_id` |
  |---|---|---|
  | `DEPOSIT` | `NULL` | preenchido |
  | `WITHDRAW` | preenchido | `NULL` |
  | `PIX_TRANSFER` | preenchido | preenchido, e diferente de `source_account_id` |

- Em `PIX_TRANSFER`, `source_account_id != destination_account_id` — validado explicitamente dentro
  de `validate_transaction_shape()`.

**Exceção relacionada:** `InvalidTransactionShapeError`.

## Diagrama de classes

```mermaid
classDiagram
    class Customer {
        +int id
        +str name
        +str email
        +str cpf
        +str password_hash
        +str role
        +datetime created_at
    }
    class Account {
        +int id
        +int customer_id
        +str agency
        +str number
        +str label
        +int balance_cents
        +datetime created_at
        +deposit(amount_cents)
        +withdraw(amount_cents)
    }
    class PixKey {
        +int id
        +int account_id
        +str type
        +str value
        +datetime created_at
    }
    class Transaction {
        <<persistence-only, sem entidade de domínio>>
        +int id
        +int source_account_id
        +int destination_account_id
        +str type
        +int amount_cents
        +str description
        +datetime created_at
    }

    Customer "1" --> "N" Account : owns
    Account "1" --> "N" PixKey : has
    Account "1" --> "N" Transaction : source_account_id
    Account "1" --> "N" Transaction : destination_account_id
```

## Exemplos concretos de regras de negócio

**Valor inválido (depósito ou saque):**
```python
account.deposit(-100)   # → InvalidAmountError("amount_cents must be greater than zero, got -100")
account.withdraw(0)     # → InvalidAmountError(...)
```

**Saldo insuficiente:**
```python
# account.balance_cents == 500
account.withdraw(1000)  # → InsufficientBalanceError(account_id, 1000, 500)
```

**Chave Pix duplicada:**
```python
# já existe uma PixKey com value="maria@example.com"
pix_key_service.create(account_id=7, key_type="EMAIL", value="maria@example.com")
# → DuplicatePixKeyError("pix key value maria@example.com already registered")
```

**Transferência para a própria conta:**
```python
# source_account_id == destination.id
pix_transfer_service.transfer(source_account_id=10, pix_key_value="10-own-key", amount_cents=100)
# → SameAccountTransferError("cannot transfer to the same account (10)")
```

## Sobre dinheiro: por que não existe uma classe `Money`

Não há `Money` como *value object* separado. Dinheiro é representado por `int` (centavos) em todas
as camadas do backend — domínio, serviço e API. `docs/specs/02-domain-model.md` cogita um possível
`app/domain/money.py` com pequenos helpers; **esse arquivo não existe na implementação atual** — não
foi necessário, porque nenhuma conversão de centavos acontece em Python. A única formatação de
centavos para reais (`1050` → `"R$ 10,50"`) do projeto inteiro é `formatCents()`, em
`app/static/js/api.js`, no frontend (ver `08-frontend.md`). Ver `05-banco-de-dados.md` para a
justificativa completa de por que dinheiro é sempre inteiro em centavos.

## Exceções de domínio (completo)

Todas em `app/domain/exceptions.py`, herdando de `DomainError`, sem qualquer dependência de
SQLAlchemy ou FastAPI:

| Exceção | Situação |
|---|---|
| `CustomerNotFoundError` | cliente não existe |
| `AccountNotFoundError` | conta não existe |
| `PixKeyNotFoundError` | chave Pix não existe |
| `DuplicateEmailError` | email já cadastrado |
| `DuplicateCpfError` | CPF já cadastrado |
| `DuplicatePixKeyError` | valor de chave Pix já cadastrado |
| `DuplicateAccountNumberError` | número de conta já cadastrado |
| `InvalidCpfError` | CPF com formato/dígito inválido |
| `InvalidPixKeyError` | valor não bate com o formato esperado do tipo |
| `InvalidAmountError` | `amount_cents <= 0` |
| `InsufficientBalanceError` | saque/transferência maior que o saldo |
| `SameAccountTransferError` | transferência para a própria conta |
| `CustomerHasAccountsError` | exclusão de cliente com contas associadas |
| `AccountHasDependenciesError` | exclusão de conta com saldo, chaves ou transações |
| `InvalidTransactionShapeError` | forma de `Transaction` incompatível com o `type` |
| `NotAuthenticatedError` | sem sessão válida |
| `InvalidCredentialsError` | email/senha incorretos no login |
| `ForbiddenError` | autenticado, mas sem permissão para a operação |

O mapeamento de cada exceção para um código HTTP está em `06-api.md`.
