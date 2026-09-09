import pytest

from app.adapters.outbound.persistence import models  # noqa: F401
from app.adapters.outbound.persistence.account_repository_sqlalchemy import (
    AccountRepositorySqlAlchemy,
)
from app.adapters.outbound.persistence.customer_repository_sqlalchemy import (
    CustomerRepositorySqlAlchemy,
)
from app.adapters.outbound.persistence.pix_key_repository_sqlalchemy import (
    PixKeyRepositorySqlAlchemy,
)
from app.adapters.outbound.persistence.transaction_repository_sqlalchemy import (
    TransactionRepositorySqlAlchemy,
)
from app.application.services.account_service import AccountService
from app.application.services.customer_service import CustomerService
from app.application.services.pix_key_service import PixKeyService
from app.domain.exceptions import (
    AccountNotFoundError,
    DuplicatePixKeyError,
    InvalidPixKeyError,
    PixKeyNotFoundError,
)
from tests.helpers import generate_valid_cpf

VALID_CPF = generate_valid_cpf("529982247")


def make_account(db_session):
    customer_service = CustomerService(
        customer_repo=CustomerRepositorySqlAlchemy(db_session),
        account_repo=AccountRepositorySqlAlchemy(db_session),
    )
    customer = customer_service.create(name="Maria Silva", email="maria@example.com", cpf=VALID_CPF)

    account_service = AccountService(
        account_repo=AccountRepositorySqlAlchemy(db_session),
        customer_repo=CustomerRepositorySqlAlchemy(db_session),
        transaction_repo=TransactionRepositorySqlAlchemy(db_session),
    )
    return account_service.create(customer_id=customer.id, agency="0001", number="123456")


def make_service(db_session) -> PixKeyService:
    return PixKeyService(
        pix_key_repo=PixKeyRepositorySqlAlchemy(db_session),
        account_repo=AccountRepositorySqlAlchemy(db_session),
    )


def test_register_pix_key_success(db_session):
    account = make_account(db_session)
    service = make_service(db_session)

    pix_key = service.create(account_id=account.id, key_type="EMAIL", value="maria@example.com")

    assert pix_key.id is not None
    assert pix_key.type == "EMAIL"


def test_register_pix_key_missing_account_raises_error(db_session):
    service = make_service(db_session)

    with pytest.raises(AccountNotFoundError):
        service.create(account_id=999, key_type="EMAIL", value="maria@example.com")


def test_register_pix_key_invalid_format_raises_error(db_session):
    account = make_account(db_session)
    service = make_service(db_session)

    with pytest.raises(InvalidPixKeyError):
        service.create(account_id=account.id, key_type="EMAIL", value="not-an-email")


def test_register_pix_key_duplicate_value_raises_error(db_session):
    account = make_account(db_session)
    service = make_service(db_session)
    service.create(account_id=account.id, key_type="EMAIL", value="maria@example.com")

    with pytest.raises(DuplicatePixKeyError):
        service.create(account_id=account.id, key_type="EMAIL", value="maria@example.com")


def test_update_pix_key_with_revalidation(db_session):
    account = make_account(db_session)
    service = make_service(db_session)
    pix_key = service.create(account_id=account.id, key_type="EMAIL", value="maria@example.com")

    updated = service.update(pix_key.id, key_type=None, value="maria.s@example.com")

    assert updated.value == "maria.s@example.com"


def test_update_pix_key_to_invalid_format_raises_error(db_session):
    account = make_account(db_session)
    service = make_service(db_session)
    pix_key = service.create(account_id=account.id, key_type="EMAIL", value="maria@example.com")

    with pytest.raises(InvalidPixKeyError):
        service.update(pix_key.id, key_type=None, value="not-an-email")


def test_delete_pix_key(db_session):
    account = make_account(db_session)
    service = make_service(db_session)
    pix_key = service.create(account_id=account.id, key_type="EMAIL", value="maria@example.com")

    service.delete(pix_key.id)

    with pytest.raises(PixKeyNotFoundError):
        service.get(pix_key.id)
