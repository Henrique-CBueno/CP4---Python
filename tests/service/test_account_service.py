import pytest

from app.adapters.outbound.persistence import models  # noqa: F401
from app.adapters.outbound.persistence.account_repository_sqlalchemy import (
    AccountRepositorySqlAlchemy,
)
from app.adapters.outbound.persistence.customer_repository_sqlalchemy import (
    CustomerRepositorySqlAlchemy,
)
from app.adapters.outbound.persistence.models import Account as AccountModel
from app.adapters.outbound.persistence.models import PixKey as PixKeyModel
from app.adapters.outbound.persistence.models import Transaction as TransactionModel
from app.adapters.outbound.persistence.transaction_repository_sqlalchemy import (
    TransactionRepositorySqlAlchemy,
)
from app.application.services.account_service import AccountService
from app.application.services.customer_service import CustomerService
from app.domain.exceptions import (
    AccountHasDependenciesError,
    AccountNotFoundError,
    CustomerNotFoundError,
    DuplicateAccountNumberError,
    InsufficientBalanceError,
    InvalidAmountError,
)
from tests.helpers import generate_valid_cpf

VALID_CPF = generate_valid_cpf("529982247")


def make_customer(db_session):
    customer_service = CustomerService(
        customer_repo=CustomerRepositorySqlAlchemy(db_session),
        account_repo=AccountRepositorySqlAlchemy(db_session),
    )
    return customer_service.create(name="Maria Silva", email="maria@example.com", cpf=VALID_CPF, password="Password123")


def make_service(db_session) -> AccountService:
    return AccountService(
        account_repo=AccountRepositorySqlAlchemy(db_session),
        customer_repo=CustomerRepositorySqlAlchemy(db_session),
        transaction_repo=TransactionRepositorySqlAlchemy(db_session),
    )


def test_create_account_success(db_session):
    customer = make_customer(db_session)
    service = make_service(db_session)

    account = service.create(customer_id=customer.id, agency="0001", number="123456")

    assert account.id is not None
    assert account.balance_cents == 0


def test_create_account_with_missing_customer_raises_not_found(db_session):
    service = make_service(db_session)

    with pytest.raises(CustomerNotFoundError):
        service.create(customer_id=999, agency="0001", number="123456")


def test_create_account_with_duplicate_number_raises_error(db_session):
    customer = make_customer(db_session)
    service = make_service(db_session)
    service.create(customer_id=customer.id, agency="0001", number="123456")

    with pytest.raises(DuplicateAccountNumberError):
        service.create(customer_id=customer.id, agency="0002", number="123456")


def test_update_account_agency_and_label(db_session):
    customer = make_customer(db_session)
    service = make_service(db_session)
    account = service.create(customer_id=customer.id, agency="0001", number="123456")

    updated = service.update(account.id, agency="0002", label="Conta principal")

    assert updated.agency == "0002"
    assert updated.label == "Conta principal"


def test_delete_account_without_dependencies(db_session):
    customer = make_customer(db_session)
    service = make_service(db_session)
    account = service.create(customer_id=customer.id, agency="0001", number="123456")

    service.delete(account.id)

    with pytest.raises(AccountNotFoundError):
        service.get(account.id)


def test_delete_account_with_balance_raises_error(db_session):
    customer = make_customer(db_session)
    service = make_service(db_session)
    account = service.create(customer_id=customer.id, agency="0001", number="123456")

    model = db_session.get(AccountModel, account.id)
    model.balance_cents = 500
    db_session.flush()

    with pytest.raises(AccountHasDependenciesError):
        service.delete(account.id)


def test_delete_account_with_pix_key_raises_error(db_session):
    customer = make_customer(db_session)
    service = make_service(db_session)
    account = service.create(customer_id=customer.id, agency="0001", number="123456")

    db_session.add(PixKeyModel(account_id=account.id, type="EMAIL", value="maria@example.com"))
    db_session.flush()

    with pytest.raises(AccountHasDependenciesError):
        service.delete(account.id)


def test_delete_account_with_transaction_raises_error(db_session):
    customer = make_customer(db_session)
    service = make_service(db_session)
    account = service.create(customer_id=customer.id, agency="0001", number="123456")

    db_session.add(
        TransactionModel(
            source_account_id=None,
            destination_account_id=account.id,
            type="DEPOSIT",
            amount_cents=1000,
        )
    )
    db_session.flush()

    with pytest.raises(AccountHasDependenciesError):
        service.delete(account.id)


def test_deposit_success(db_session):
    customer = make_customer(db_session)
    service = make_service(db_session)
    account = service.create(customer_id=customer.id, agency="0001", number="123456")

    transaction = service.deposit(account.id, 1000)

    assert transaction.type == "DEPOSIT"
    assert transaction.source_account_id is None
    assert transaction.destination_account_id == account.id
    assert service.get(account.id).balance_cents == 1000


def test_deposit_invalid_amount_raises_error(db_session):
    customer = make_customer(db_session)
    service = make_service(db_session)
    account = service.create(customer_id=customer.id, agency="0001", number="123456")

    with pytest.raises(InvalidAmountError):
        service.deposit(account.id, 0)


def test_withdraw_success(db_session):
    customer = make_customer(db_session)
    service = make_service(db_session)
    account = service.create(customer_id=customer.id, agency="0001", number="123456")
    service.deposit(account.id, 1000)

    transaction = service.withdraw(account.id, 400)

    assert transaction.type == "WITHDRAW"
    assert transaction.source_account_id == account.id
    assert transaction.destination_account_id is None
    assert service.get(account.id).balance_cents == 600


def test_withdraw_insufficient_balance_raises_error(db_session):
    customer = make_customer(db_session)
    service = make_service(db_session)
    account = service.create(customer_id=customer.id, agency="0001", number="123456")

    with pytest.raises(InsufficientBalanceError):
        service.withdraw(account.id, 100)
