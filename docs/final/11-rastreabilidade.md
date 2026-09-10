# 11 — Rastreabilidade

Este documento conecta, ponta a ponta, cada exigência acadêmica a uma funcionalidade concreta, ao
endpoint que a expõe, ao Service que a implementa, ao mecanismo de persistência, à parte do frontend
que a consome e ao teste automatizado que a comprova. Todos os caminhos abaixo são caminhos de
código reais, verificados neste repositório — não descrições genéricas.

## Exemplo de leitura da matriz

> "Frontend consome a API"
> → página **Clientes**
> → `GET /api/customers`
> → `CustomerService.list()`
> → `CustomerRepositorySqlAlchemy.list()`
> → `customers.js::loadCustomers()`
> → `tests/api/test_customers_api.py::test_list_customers`

## Matriz completa

| Requisito Acadêmico | Funcionalidade | Endpoint da API | Service | Persistência (Port → Adapter) | Frontend | Teste |
|---|---|---|---|---|---|---|
| Frontend consome a API | Listar clientes | `GET /api/customers` | `CustomerService.list()` | `CustomerRepository` → `CustomerRepositorySqlAlchemy` | `customers.js::loadCustomers()` | `tests/api/test_customers_api.py::test_list_customers` |
| CRUD completo | Cadastrar cliente | `POST /api/customers` | `CustomerService.create()` | `CustomerRepository.add()` → `CustomerRepositorySqlAlchemy.add()` | `customers.js` (submit de `#customer-form`) | `tests/api/test_customers_api.py::test_create_and_get_customer` |
| CRUD completo | Atualizar cliente | `PUT /api/customers/{id}` | `CustomerService.update()` | `CustomerRepositorySqlAlchemy.update()` | `customers.js` (modo edição do mesmo formulário) | `tests/api/test_customers_api.py::test_update_customer` |
| CRUD completo | Remover cliente | `DELETE /api/customers/{id}` | `CustomerService.delete()` | `CustomerRepositorySqlAlchemy.delete()` | `customers.js` (botão "remover") | `tests/api/test_customers_api.py::test_delete_customer` |
| Regra de negócio: exclusão bloqueada | Cliente com contas não pode ser removido | `DELETE /api/customers/{id}` → `409` | `CustomerService.delete()` (`CustomerHasAccountsError`) | `AccountRepository.list_by_customer()` (checagem) | mensagem de erro exibida em `#customers-error` | `tests/service/test_customer_service.py::test_delete_customer_with_accounts_raises_error` |
| Pelo menos 2 modelos relacionados | Criar conta vinculada a um cliente | `POST /api/accounts` | `AccountService.create()` | `AccountRepository.add()` → `AccountRepositorySqlAlchemy.add()` | `accounts.js` (submit de `#account-form`) | `tests/api/test_accounts_api.py::test_create_and_get_account` |
| CRUD completo | Listar contas | `GET /api/accounts` | `AccountService.list()` / `.list_by_customer()` | `AccountRepositorySqlAlchemy.list()` | `accounts.js::loadAccounts()` | `tests/api/test_authorization.py::test_customer_sees_only_own_accounts_in_list` |
| CRUD completo | Atualizar conta (`agency`/`label`) | `PUT /api/accounts/{id}` | `AccountService.update()` | `AccountRepositorySqlAlchemy.update()` | `accounts.js` (modo edição) | `tests/api/test_accounts_api.py::test_update_account_agency_and_label` |
| CRUD completo | Remover conta | `DELETE /api/accounts/{id}` | `AccountService.delete()` | `AccountRepositorySqlAlchemy.delete()` | `accounts.js` (botão "remover") | `tests/api/test_accounts_api.py::test_delete_account_without_dependencies` |
| Persistência em SQLite + regra de negócio | Consultar saldo | `GET /api/accounts/{id}/balance` | `AccountService.get()` | `AccountRepositorySqlAlchemy.get_by_id()` | `account_detail.js::renderAccount()` | `tests/api/test_accounts_api.py::test_get_account_balance` |
| Operação financeira específica | Depositar | `POST /api/accounts/{id}/deposit` | `AccountService.deposit()` → `Account.deposit()` (domínio) | `TransactionRepository.add()` → `TransactionRepositorySqlAlchemy.add()` | `account_detail.js` (`#deposit-form`) | `tests/service/test_account_service.py::test_deposit_success` |
| Operação financeira específica | Sacar | `POST /api/accounts/{id}/withdraw` | `AccountService.withdraw()` → `Account.withdraw()` (domínio) | `TransactionRepositorySqlAlchemy.add()` | `account_detail.js` (`#withdraw-form`) | `tests/service/test_account_service.py::test_withdraw_success` |
| Regra de negócio: saldo insuficiente | Saque maior que o saldo é rejeitado | `POST /api/accounts/{id}/withdraw` → `400` | `Account.withdraw()` levanta `InsufficientBalanceError` | — (nenhuma escrita ocorre) | erro exibido em `#account-detail-error` | `tests/service/test_account_service.py::test_withdraw_insufficient_balance_raises_error` |
| CRUD completo | Cadastrar chave Pix | `POST /api/pix-keys` | `PixKeyService.create()` | `PixKeyRepository.add()` → `PixKeyRepositorySqlAlchemy.add()` | `account_detail.js` (`#pix-key-form`) | `tests/api/test_pix_keys_api.py::test_create_and_get_pix_key` |
| Regra de negócio: unicidade | Chave Pix duplicada é rejeitada | `POST /api/pix-keys` → `409` | `PixKeyService.create()` (`DuplicatePixKeyError`) | `PixKeyRepository.get_by_value()` (checagem) | erro exibido no formulário de chave Pix | `tests/service/test_pix_key_service.py::test_register_pix_key_duplicate_value_raises_error` |
| CRUD completo | Atualizar chave Pix | `PUT /api/pix-keys/{id}` | `PixKeyService.update()` | `PixKeyRepositorySqlAlchemy.update()` | `account_detail.js` (modo edição da chave) | `tests/service/test_pix_key_service.py::test_update_pix_key_with_revalidation` |
| CRUD completo | Remover chave Pix | `DELETE /api/pix-keys/{id}` | `PixKeyService.delete()` | `PixKeyRepositorySqlAlchemy.delete()` | `account_detail.js` (botão "remover" da chave) | `tests/api/test_pix_keys_api.py::test_delete_pix_key` |
| Operação financeira específica | Transferir via chave Pix | `POST /api/pix/transfers` | `PixTransferService.transfer()` | `AccountRepositorySqlAlchemy.update()` ×2 + `TransactionRepositorySqlAlchemy.add()` | `pix_transfer.js` (`#pix-transfer-form`) | `tests/service/test_pix_transfer_service.py::test_transfer_success_updates_both_accounts` |
| Regra de negócio: mesma conta | Transferência para si mesmo é rejeitada | `POST /api/pix/transfers` → `400` | `PixTransferService.transfer()` (`SameAccountTransferError`) | — | erro exibido em `#pix-transfer-error` | `tests/service/test_pix_transfer_service.py::test_transfer_to_same_account_raises_error` |
| Atomicidade (RNF05) | Falha no meio da transferência não deixa estado parcial | `POST /api/pix/transfers` | `PixTransferService.transfer()` + commit único em `get_db()` | `flush()` sem `commit()` até o fim da requisição | (não observável diretamente na UI — comportamento de backend) | `tests/service/test_pix_transfer_service.py::test_transfer_atomicity_on_failure` |
| Operação financeira específica | Consultar extrato | `GET /api/accounts/{id}/transactions` | `AccountService.get_statement()` | `TransactionRepository.list_by_account()` → `TransactionRepositorySqlAlchemy.list_by_account()` | `account_detail.js::loadStatement()` | `tests/service/test_statement_service.py::test_statement_reflects_deposit_withdraw_and_transfer` |
| Autenticação (extra) | Login por sessão | `POST /api/auth/login` | `CustomerService.authenticate()` | `CustomerRepository.get_by_email()` | `login.js` | `tests/api/test_auth_api.py::test_login_success` |
| Autorização (extra) | Cliente só opera as próprias contas | qualquer endpoint de `Account`/`PixKey`/transferência | `ensure_account_owner_or_admin()` (Controller, não Service) | — (checagem antes da chamada ao Service) | `accounts.js`/`account_detail.js` (controles condicionados a `isAdmin`) | `tests/api/test_authorization.py::test_customer_cannot_deposit_in_anothers_account` |
| Dados persistidos em SQLite | Dado sobrevive entre requisições reais (não só dentro de um teste com sessão compartilhada) | `POST` + `GET /api/customers` em requisições separadas | `CustomerService.create()` + `.get()` | `SessionLocal` real de `app/infrastructure/db.py` (não `dependency_overrides`) | — | `tests/api/test_persistence_wiring.py::test_customer_persists_across_separate_requests` |

## Cobertura por tipo de teste

A rastreabilidade acima mistura testes de API e de Service deliberadamente — cada regra de negócio
tem, tipicamente, **dois** pontos de cobertura: um teste de `tests/service/` que a exercita
diretamente contra o Service (sem HTTP), e um teste de `tests/api/` equivalente que confirma o
código HTTP correto fim a fim. Ver `09-testes.md` para a listagem completa por arquivo.

## Como usar este documento na apresentação

Esta matriz é o material de apoio mais direto para responder "onde isso está implementado?" ou "como
vocês testaram isso?" durante a arguição — cada linha é um caminho de código que pode ser aberto ao
vivo. Ver `12-guia-de-apresentacao.md` para um roteiro que usa exatamente essas linhas.
