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
from app.domain.exceptions import (
    AccountNotFoundError,
    InsufficientBalanceError,
    InvalidAmountError,
    PixKeyNotFoundError,
    SameAccountTransferError,
)
from tests.helpers import generate_valid_cpf


def make_account(db_session, cpf, email, number):
    customer_service = CustomerService(
        customer_repo=CustomerRepositorySqlAlchemy(db_session),
        account_repo=AccountRepositorySqlAlchemy(db_session),
    )
    customer = customer_service.create(name="Cliente", email=email, cpf=cpf)

    account_service = AccountService(
        account_repo=AccountRepositorySqlAlchemy(db_session),
        customer_repo=CustomerRepositorySqlAlchemy(db_session),
        transaction_repo=TransactionRepositorySqlAlchemy(db_session),
    )
    account = account_service.create(customer_id=customer.id, agency="0001", number=number)
    return account, account_service


def make_pix_key_service(db_session) -> PixKeyService:
    return PixKeyService(
        pix_key_repo=PixKeyRepositorySqlAlchemy(db_session),
        account_repo=AccountRepositorySqlAlchemy(db_session),
    )


def make_transfer_service(db_session) -> PixTransferService:
    return PixTransferService(
        account_repo=AccountRepositorySqlAlchemy(db_session),
        pix_key_repo=PixKeyRepositorySqlAlchemy(db_session),
        transaction_repo=TransactionRepositorySqlAlchemy(db_session),
    )


def test_transfer_success_updates_both_accounts(db_session):
    source, source_service = make_account(
        db_session, generate_valid_cpf("529982247"), "source@example.com", "111111"
    )
    destination, _ = make_account(
        db_session, generate_valid_cpf("111444777"), "destination@example.com", "222222"
    )
    pix_key_service = make_pix_key_service(db_session)
    pix_key = pix_key_service.create(
        account_id=destination.id, key_type="EMAIL", value="destination@example.com"
    )
    source_service.deposit(source.id, 1000)

    transfer_service = make_transfer_service(db_session)
    transaction = transfer_service.transfer(
        source_account_id=source.id, pix_key_value=pix_key.value, amount_cents=400
    )

    assert transaction.type == "PIX_TRANSFER"
    assert transaction.source_account_id == source.id
    assert transaction.destination_account_id == destination.id
    assert source_service.get(source.id).balance_cents == 600
    assert source_service.get(destination.id).balance_cents == 400


def test_transfer_pix_key_not_found_raises_error(db_session):
    source, source_service = make_account(
        db_session, generate_valid_cpf("529982247"), "source@example.com", "111111"
    )
    source_service.deposit(source.id, 1000)
    transfer_service = make_transfer_service(db_session)

    with pytest.raises(PixKeyNotFoundError):
        transfer_service.transfer(
            source_account_id=source.id, pix_key_value="unknown@example.com", amount_cents=100
        )


def test_transfer_insufficient_balance_raises_error(db_session):
    source, _ = make_account(
        db_session, generate_valid_cpf("529982247"), "source@example.com", "111111"
    )
    destination, _ = make_account(
        db_session, generate_valid_cpf("111444777"), "destination@example.com", "222222"
    )
    pix_key_service = make_pix_key_service(db_session)
    pix_key = pix_key_service.create(
        account_id=destination.id, key_type="EMAIL", value="destination@example.com"
    )
    transfer_service = make_transfer_service(db_session)

    with pytest.raises(InsufficientBalanceError):
        transfer_service.transfer(
            source_account_id=source.id, pix_key_value=pix_key.value, amount_cents=100
        )


def test_transfer_to_same_account_raises_error(db_session):
    source, source_service = make_account(
        db_session, generate_valid_cpf("529982247"), "source@example.com", "111111"
    )
    source_service.deposit(source.id, 1000)
    pix_key_service = make_pix_key_service(db_session)
    pix_key = pix_key_service.create(
        account_id=source.id, key_type="EMAIL", value="source@example.com"
    )
    transfer_service = make_transfer_service(db_session)

    with pytest.raises(SameAccountTransferError):
        transfer_service.transfer(
            source_account_id=source.id, pix_key_value=pix_key.value, amount_cents=100
        )


def test_transfer_invalid_amount_raises_error(db_session):
    source, source_service = make_account(
        db_session, generate_valid_cpf("529982247"), "source@example.com", "111111"
    )
    source_service.deposit(source.id, 1000)
    transfer_service = make_transfer_service(db_session)

    with pytest.raises(InvalidAmountError):
        transfer_service.transfer(source_account_id=source.id, pix_key_value="x", amount_cents=0)


def test_transfer_missing_source_account_raises_error(db_session):
    transfer_service = make_transfer_service(db_session)

    with pytest.raises(AccountNotFoundError):
        transfer_service.transfer(
            source_account_id=999, pix_key_value="anything@example.com", amount_cents=100
        )


def test_transfer_atomicity_on_failure(db_session):
    """Se a criação do registro de Transaction falhar após os débitos/créditos
    já terem sido aplicados na sessão, um rollback deve desfazer tudo — nada
    fica em estado parcial."""

    source, source_service = make_account(
        db_session, generate_valid_cpf("529982247"), "source@example.com", "111111"
    )
    destination, _ = make_account(
        db_session, generate_valid_cpf("111444777"), "destination@example.com", "222222"
    )
    pix_key_service = make_pix_key_service(db_session)
    pix_key = pix_key_service.create(
        account_id=destination.id, key_type="EMAIL", value="destination@example.com"
    )
    source_service.deposit(source.id, 1000)
    # Confirma (commit) o estado inicial, simulando requisições anteriores já
    # concluídas com sucesso — só a operação de transferência abaixo deve ser
    # desfeita pelo rollback.
    db_session.commit()

    class BrokenTransactionRepo:
        def add(self, **kwargs):
            raise RuntimeError("simulated failure while persisting the transaction")

        def list_by_account(self, account_id):
            return []

    transfer_service = PixTransferService(
        account_repo=AccountRepositorySqlAlchemy(db_session),
        pix_key_repo=PixKeyRepositorySqlAlchemy(db_session),
        transaction_repo=BrokenTransactionRepo(),
    )

    with pytest.raises(RuntimeError):
        transfer_service.transfer(
            source_account_id=source.id, pix_key_value=pix_key.value, amount_cents=400
        )

    # Simula o que get_db() faz automaticamente ao fechar a sessão de uma
    # requisição que terminou em erro (nenhum commit é feito).
    db_session.rollback()

    account_repo = AccountRepositorySqlAlchemy(db_session)
    assert account_repo.get_by_id(source.id).balance_cents == 1000
    assert account_repo.get_by_id(destination.id).balance_cents == 0
