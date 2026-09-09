import pytest

from app.adapters.outbound.persistence import models  # noqa: F401
from app.adapters.outbound.persistence.account_repository_sqlalchemy import (
    AccountRepositorySqlAlchemy,
)
from app.adapters.outbound.persistence.customer_repository_sqlalchemy import (
    CustomerRepositorySqlAlchemy,
)
from app.adapters.outbound.persistence.transaction_repository_sqlalchemy import (
    TransactionRepositorySqlAlchemy,
)
from app.application.services.account_service import AccountService
from app.application.services.customer_service import CustomerService
from app.domain.exceptions import (
    CustomerHasAccountsError,
    CustomerNotFoundError,
    DuplicateCpfError,
    DuplicateEmailError,
    InvalidCpfError,
)
from tests.helpers import generate_valid_cpf

VALID_CPF = generate_valid_cpf("529982247")
OTHER_VALID_CPF = generate_valid_cpf("111444777")


def make_service(db_session) -> CustomerService:
    return CustomerService(
        customer_repo=CustomerRepositorySqlAlchemy(db_session),
        account_repo=AccountRepositorySqlAlchemy(db_session),
    )


def make_account_service(db_session) -> AccountService:
    return AccountService(
        account_repo=AccountRepositorySqlAlchemy(db_session),
        customer_repo=CustomerRepositorySqlAlchemy(db_session),
        transaction_repo=TransactionRepositorySqlAlchemy(db_session),
    )


def test_create_customer_success(db_session):
    service = make_service(db_session)

    customer = service.create(name="Maria Silva", email="maria@example.com", cpf=VALID_CPF, password="Password123")

    assert customer.id is not None
    assert customer.name == "Maria Silva"
    assert customer.cpf == VALID_CPF


def test_create_customer_invalid_cpf(db_session):
    service = make_service(db_session)

    with pytest.raises(InvalidCpfError):
        service.create(name="Maria Silva", email="maria@example.com", cpf="12345678900", password="Password123")


def test_create_customer_duplicate_email(db_session):
    service = make_service(db_session)
    service.create(name="Maria Silva", email="maria@example.com", cpf=VALID_CPF, password="Password123")

    with pytest.raises(DuplicateEmailError):
        service.create(name="Outro Nome", email="maria@example.com", cpf=OTHER_VALID_CPF, password="Password123")


def test_create_customer_duplicate_cpf(db_session):
    service = make_service(db_session)
    service.create(name="Maria Silva", email="maria@example.com", cpf=VALID_CPF, password="Password123")

    with pytest.raises(DuplicateCpfError):
        service.create(name="Outro Nome", email="outro@example.com", cpf=VALID_CPF, password="Password123")


def test_update_customer_name_and_email(db_session):
    service = make_service(db_session)
    customer = service.create(name="Maria Silva", email="maria@example.com", cpf=VALID_CPF, password="Password123")

    updated = service.update(customer.id, name="Maria S. Silva", email="maria.s@example.com")

    assert updated.name == "Maria S. Silva"
    assert updated.email == "maria.s@example.com"


def test_delete_customer_without_accounts(db_session):
    service = make_service(db_session)
    customer = service.create(name="Maria Silva", email="maria@example.com", cpf=VALID_CPF, password="Password123")

    service.delete(customer.id)

    with pytest.raises(CustomerNotFoundError):
        service.get(customer.id)


def test_get_missing_customer_raises_not_found(db_session):
    service = make_service(db_session)

    with pytest.raises(CustomerNotFoundError):
        service.get(999)


def test_delete_customer_with_accounts_raises_error(db_session):
    customer_service = make_service(db_session)
    account_service = make_account_service(db_session)
    customer = customer_service.create(name="Maria Silva", email="maria@example.com", cpf=VALID_CPF, password="Password123")
    account_service.create(customer_id=customer.id, agency="0001", number="123456")

    with pytest.raises(CustomerHasAccountsError):
        customer_service.delete(customer.id)
