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
from app.application.services.pix_transfer_service import PixTransferService
from app.domain.exceptions import AccountNotFoundError
from tests.helpers import generate_valid_cpf


def make_account(db_session, cpf, email, number):
    customer_service = CustomerService(
        customer_repo=CustomerRepositorySqlAlchemy(db_session),
        account_repo=AccountRepositorySqlAlchemy(db_session),
    )
    customer = customer_service.create(name="Cliente", email=email, cpf=cpf, password="Password123")

    account_service = AccountService(
        account_repo=AccountRepositorySqlAlchemy(db_session),
        customer_repo=CustomerRepositorySqlAlchemy(db_session),
        transaction_repo=TransactionRepositorySqlAlchemy(db_session),
    )
    account = account_service.create(customer_id=customer.id, agency="0001", number=number)
    return account, account_service


def test_statement_reflects_deposit_withdraw_and_transfer(db_session):
    source, source_service = make_account(
        db_session, generate_valid_cpf("529982247"), "source@example.com", "111111"
    )
    destination, dest_service = make_account(
        db_session, generate_valid_cpf("111444777"), "destination@example.com", "222222"
    )
    pix_key_service = PixKeyService(
        pix_key_repo=PixKeyRepositorySqlAlchemy(db_session),
        account_repo=AccountRepositorySqlAlchemy(db_session),
    )
    pix_key = pix_key_service.create(
        account_id=destination.id, key_type="EMAIL", value="destination@example.com"
    )

    source_service.deposit(source.id, 1000)
    source_service.withdraw(source.id, 200)

    transfer_service = PixTransferService(
        account_repo=AccountRepositorySqlAlchemy(db_session),
        pix_key_repo=PixKeyRepositorySqlAlchemy(db_session),
        transaction_repo=TransactionRepositorySqlAlchemy(db_session),
    )
    transfer_service.transfer(
        source_account_id=source.id, pix_key_value=pix_key.value, amount_cents=300
    )

    source_statement = source_service.get_statement(source.id)
    types = {t.type for t in source_statement}
    assert types == {"DEPOSIT", "WITHDRAW", "PIX_TRANSFER"}
    assert len(source_statement) == 3

    destination_statement = dest_service.get_statement(destination.id)
    assert len(destination_statement) == 1
    assert destination_statement[0].type == "PIX_TRANSFER"
    assert destination_statement[0].destination_account_id == destination.id


def test_statement_of_missing_account_raises_error(db_session):
    _, account_service = make_account(
        db_session, generate_valid_cpf("529982247"), "source@example.com", "111111"
    )

    with pytest.raises(AccountNotFoundError):
        account_service.get_statement(999)
