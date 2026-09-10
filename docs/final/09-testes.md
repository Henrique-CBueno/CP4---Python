# 09 — Testes

## Ferramentas

`pytest` + `fastapi.testclient.TestClient`. Nenhuma biblioteca de mock ou de *factory* — os testes
de serviço e de API usam Repository Adapters reais contra um SQLite temporário, nunca um repositório
falso (com uma única exceção pontual, ver "Atomicidade" abaixo).

## Banco de testes

Cada teste que precisa de banco recebe um **arquivo SQLite temporário** via fixture `tmp_path` do
próprio `pytest` — não um `sqlite:///:memory:` compartilhado, o que evitaria problemas de múltiplas
conexões/threads entre o `TestClient` e um banco em memória único.

```python
# tests/conftest.py
@pytest.fixture
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/test.db", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture
def anonymous_client(db_session):
    """TestClient sem sessão de login — para testar autenticação em si."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def client(db_session, anonymous_client):
    """TestClient já logado como admin — fixture padrão da maioria dos testes."""
    # cria um Customer com role="ADMIN" direto no repositório, faz login via
    # POST /api/auth/login, e devolve o TestClient já autenticado
    ...
```

Um detalhe real vale registrar: o `_override_get_db` usado por `anonymous_client` faz apenas `yield
db_session`, **sem** o `session.commit()` que a versão de produção (`get_db()` real) executa após o
`yield`. Isso funciona porque todas as requisições de um mesmo teste reaproveitam a **mesma**
`Session` (a mesma conexão/transação) — o que uma escreveu com `flush()` a próxima já enxerga, sem
precisar de commit entre elas. Isso é o oposto do que acontece em produção (uma `Session` nova por
requisição, ver `03-arquitetura.md`), e é justamente o que `test_persistence_wiring.py` (ver abaixo)
existe para compensar.

`tests/helpers.py::generate_valid_cpf(base_digits)` gera um CPF válido (com os dois dígitos
verificadores calculados corretamente) a partir de 9 dígitos-base — evita CPFs "mágicos" fixos
espalhados pelos testes.

## Camadas de teste

### Unit — domínio puro (`tests/unit/`)

Sem banco, sem FastAPI, sem sessão — só funções e métodos puros.

| Arquivo | O que testa |
|---|---|
| `test_validators.py` | CPF válido/inválido (dígito verificador, tamanho, dígitos repetidos), email válido/inválido, formato de chave Pix por tipo (CPF/EMAIL/PHONE/RANDOM) |
| `test_transaction_rules.py` | um caso por `type` (`DEPOSIT`/`WITHDRAW`/`PIX_TRANSFER`) validando a forma esperada de `source_account_id`/`destination_account_id`; casos inválidos levantam `InvalidTransactionShapeError` |
| `test_password_hashing.py` | hash com salt aleatório por chamada; verificação com senha correta/errada; hash malformado é rejeitado sem lançar exceção |
| `test_database_schema.py` | `Base.metadata.create_all()` cria as 4 tabelas esperadas |

`Account.deposit()`/`.withdraw()` (valor inválido, saldo insuficiente) não têm um arquivo próprio em
`tests/unit/` — são cobertos indiretamente pelos testes de `tests/service/test_account_service.py`
(que exercitam o mesmo método de domínio através do Service).

### Service (`tests/service/`)

Com SQLite temporário real, sem mocks (exceto no teste de atomicidade):

| Arquivo | Cenários cobertos |
|---|---|
| `test_customer_service.py` | criação válida; CPF inválido; email duplicado; CPF duplicado; atualização de nome/email; exclusão sem contas (sucesso); exclusão com contas (`CustomerHasAccountsError`); busca de cliente inexistente (`CustomerNotFoundError`) |
| `test_account_service.py` | criação válida; cliente inexistente; número duplicado; atualização de `agency`/`label`; depósito (sucesso e valor inválido); saque (sucesso e saldo insuficiente); exclusão sem dependências (sucesso); exclusão com saldo, com chave Pix, ou com transação associada (erro nos três casos) |
| `test_pix_key_service.py` | cadastro válido; conta inexistente; formato inválido; valor duplicado; atualização com revalidação; atualização para formato inválido; remoção |
| `test_pix_transfer_service.py` | transferência válida (ambas as contas atualizadas); chave inexistente; saldo insuficiente; mesma conta; valor inválido; conta de origem inexistente; **atomicidade** (ver seção dedicada abaixo) |
| `test_statement_service.py` | extrato reflete depósitos, saques e transferências (como origem e como destino); extrato de conta inexistente (`AccountNotFoundError`) |

### API (`tests/api/`)

Com `TestClient`, cobrindo os fluxos ponta a ponta e os códigos HTTP documentados em `06-api.md`:

| Arquivo | Cenários cobertos |
|---|---|
| `test_customers_api.py` | CRUD completo; email duplicado (`409`); CPF inválido (`422`); campos não permitidos rejeitados; cliente inexistente (`404`) |
| `test_accounts_api.py` | criação e consulta; cliente inexistente; número duplicado; `PUT` rejeita `balance_cents` no corpo; atualização de `agency`/`label`; exclusão sem dependências; listagem de contas de um cliente; depósito e saque (sucesso e erro) |
| `test_pix_keys_api.py` | criação e consulta; conta inexistente; formato inválido; valor duplicado; `PUT` rejeita campos não permitidos; remoção; listagem por conta; exclusão de conta bloqueada por chave Pix associada |
| `test_pix_transfer_api.py` | transferência bem-sucedida; chave não encontrada (`404`); saldo insuficiente (`400`); mesma conta (`400`); valor inválido (`400`) |
| `test_statement_api.py` | extrato lista depósito e saque corretamente; conta inexistente (`404`) |
| `test_auth_api.py` | login bem-sucedido; senha errada (`401`); email desconhecido (`401`); `GET /me` sem sessão (`401`); `GET /me` com sessão; logout limpa a sessão |
| `test_authorization.py` | cliente não pode listar todos os clientes; cliente não pode criar conta; cliente não vê conta de outro; cliente vê e deposita na própria conta; admin deposita em conta de qualquer cliente; cliente não deposita em conta alheia; listagem de contas já filtrada por cliente; cliente não edita/remove chave Pix de conta alheia; endpoint de contas exige autenticação |
| `test_persistence_wiring.py` | dado persiste entre duas requisições **genuinamente separadas** (sessões distintas), usando a wiring real de `get_db()`/`SessionLocal`, não o `dependency_overrides` compartilhado do fixture `client` — ver nota acima sobre a diferença de sessão entre teste e produção |
| `test_web_pages.py` | as 5 páginas HTML protegidas (dashboard, customers, accounts, account_detail, pix_transfer) respondem `200` para um usuário autenticado |

## Atomicidade — como o teste comprova o rollback

`tests/service/test_pix_transfer_service.py::test_transfer_atomicity_on_failure` é o único teste do
projeto que usa um repositório falso, deliberadamente:

```python
class BrokenTransactionRepo:
    def add(self, **kwargs):
        raise RuntimeError("simulated failure while persisting the transaction")
    def list_by_account(self, account_id):
        return []
```

O teste deposita 1000 centavos na conta de origem e **confirma esse estado inicial**
(`db_session.commit()`) — simulando uma requisição anterior já concluída com sucesso. Em seguida,
monta um `PixTransferService` com o `BrokenTransactionRepo` no lugar do repositório real de
`Transaction` e chama `transfer()`. O débito e o crédito acontecem normalmente em memória e são
enviados ao banco via `flush()` — mas a criação da `Transaction` levanta `RuntimeError` antes de
qualquer commit. O teste então chama `db_session.rollback()` explicitamente, simulando exatamente o
que `get_db()` faz sozinho quando uma exceção escapa de uma requisição real (ver
`03-arquitetura.md`), e confirma:

```python
assert account_repo.get_by_id(source.id).balance_cents == 1000  # não foi debitado
assert account_repo.get_by_id(destination.id).balance_cents == 0  # não foi creditado
```

Ou seja: o teste não verifica só que uma exceção foi levantada — verifica que o **estado do banco**,
depois do rollback, é idêntico ao estado antes da tentativa de transferência.

## Exemplos de regras de negócio testadas

| Regra | Onde é testada |
|---|---|
| Valor inválido (`amount_cents <= 0`) | `test_account_service.py::test_deposit_invalid_amount_raises_error`, `test_pix_transfer_service.py::test_transfer_invalid_amount_raises_error` |
| Saldo insuficiente | `test_account_service.py::test_withdraw_insufficient_balance_raises_error`, `test_pix_transfer_service.py::test_transfer_insufficient_balance_raises_error` |
| Chave Pix duplicada | `test_pix_key_service.py::test_register_pix_key_duplicate_value_raises_error` |
| Chave Pix inexistente | `test_pix_transfer_service.py::test_transfer_pix_key_not_found_raises_error` |
| Transferência para a própria conta | `test_pix_transfer_service.py::test_transfer_to_same_account_raises_error` |
| Persistência da transação | `test_account_service.py::test_deposit_success` (verifica `Transaction` criada), `test_statement_service.py` |
| Consistência do saldo | `test_account_service.py::test_deposit_success`/`test_withdraw_success`, `test_pix_transfer_service.py::test_transfer_success_updates_both_accounts` |
| Fluxos CRUD | `test_customers_api.py`, `test_accounts_api.py`, `test_pix_keys_api.py` |

## Requisito / Regra → Teste

| Requisito / Regra | Arquivo de teste | Cenário |
|---|---|---|
| Criação de cliente | `tests/service/test_customer_service.py` | `test_create_customer_success` |
| CPF inválido rejeitado | `tests/unit/test_validators.py` | `test_cpf_with_wrong_check_digit_is_rejected` |
| Email/CPF duplicado | `tests/service/test_customer_service.py` | `test_create_customer_duplicate_email`, `test_create_customer_duplicate_cpf` |
| Cliente com contas não pode ser removido | `tests/service/test_customer_service.py` | `test_delete_customer_with_accounts_raises_error` |
| Criação de conta | `tests/service/test_account_service.py` | `test_create_account_success` |
| Número de conta duplicado | `tests/service/test_account_service.py` | `test_create_account_with_duplicate_number_raises_error` |
| Depósito válido | `tests/service/test_account_service.py` | `test_deposit_success` |
| Depósito inválido | `tests/service/test_account_service.py` | `test_deposit_invalid_amount_raises_error` |
| Saque válido | `tests/service/test_account_service.py` | `test_withdraw_success` |
| Saque sem saldo suficiente | `tests/service/test_account_service.py` | `test_withdraw_insufficient_balance_raises_error` |
| Conta com dependências não pode ser removida | `tests/service/test_account_service.py` | `test_delete_account_with_balance_raises_error`, `test_delete_account_with_pix_key_raises_error`, `test_delete_account_with_transaction_raises_error` |
| Cadastro de chave Pix | `tests/service/test_pix_key_service.py` | `test_register_pix_key_success` |
| Chave Pix duplicada | `tests/service/test_pix_key_service.py` | `test_register_pix_key_duplicate_value_raises_error` |
| Formato de chave por tipo | `tests/unit/test_validators.py` | `test_pix_key_random_requires_uuid_format` (e equivalentes para CPF/EMAIL/PHONE) |
| Transferência Pix válida | `tests/service/test_pix_transfer_service.py` | `test_transfer_success_updates_both_accounts` |
| Chave inexistente (transferência) | `tests/service/test_pix_transfer_service.py` | `test_transfer_pix_key_not_found_raises_error` |
| Saldo insuficiente (transferência) | `tests/service/test_pix_transfer_service.py` | `test_transfer_insufficient_balance_raises_error` |
| Transferência para a própria conta | `tests/service/test_pix_transfer_service.py` | `test_transfer_to_same_account_raises_error` |
| Atomicidade da transferência | `tests/service/test_pix_transfer_service.py` | `test_transfer_atomicity_on_failure` |
| Forma de `Transaction` por `type` | `tests/unit/test_transaction_rules.py` | `test_deposit_requires_only_destination`, `test_withdraw_requires_only_source`, `test_pix_transfer_requires_both_accounts` (e os equivalentes "inválido") |
| Extrato reflete todas as movimentações | `tests/service/test_statement_service.py` | `test_statement_reflects_deposit_withdraw_and_transfer` |
| Autorização: cliente só vê/opera as próprias contas | `tests/api/test_authorization.py` | `test_customer_sees_only_own_accounts_in_list`, `test_customer_cannot_deposit_in_anothers_account` |
| Autorização: admin opera qualquer conta | `tests/api/test_authorization.py` | `test_admin_can_deposit_in_any_account` |
| Persistência sobrevive entre requisições reais | `tests/api/test_persistence_wiring.py` | `test_customer_persists_across_separate_requests` |
| Páginas HTML protegidas exigem sessão | `tests/api/test_web_pages.py` | `test_dashboard_page_returns_200` (e equivalentes por página) |

## Fora da suíte `pytest`: demonstração Playwright

`scripts/e2e_demo.py` simula, pela interface web real (não pela API direto), uma jornada completa:
admin cadastra dois clientes e abre contas, deposita, cadastra uma chave `RANDOM`, o primeiro
cliente loga e opera a própria conta, confirma que não vê o link "Clientes" nem contas de terceiros,
e o extrato reflete tudo. Sobe uma instância isolada da aplicação (porta e banco SQLite temporários).
É útil como demonstração visual (inclusive para a apresentação oral, ver `12-guia-de-apresentacao.md`)
e captura screenshots de cada etapa em `playwright-artifacts/`, mas **não é executado como parte da
suíte `pytest`** — é um script independente (`python -m scripts.e2e_demo`).

## Definição de pronto

`pytest` (a partir da raiz do projeto) executa toda a suíte listada acima sem falhas antes de
qualquer entrega ser considerada concluída — os bancos de dados usados são temporários por teste e
nunca tocam o `bank.db` real usado pela aplicação em execução.
