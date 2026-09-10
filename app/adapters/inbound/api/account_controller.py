from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.adapters.inbound.api.auth_dependencies import get_current_customer
from app.adapters.inbound.api.authorization import ensure_account_owner_or_admin, ensure_admin
from app.adapters.inbound.api.pix_key_controller import get_pix_key_service
from app.adapters.inbound.api.schemas import (
    AccountCreate,
    AccountRead,
    AccountUpdate,
    DepositRequest,
    PixKeyRead,
    TransactionRead,
    WithdrawRequest,
)
from app.adapters.outbound.persistence.account_repository_sqlalchemy import (
    AccountRepositorySqlAlchemy,
)
from app.adapters.outbound.persistence.customer_repository_sqlalchemy import (
    CustomerRepositorySqlAlchemy,
)
from app.adapters.outbound.persistence.transaction_repository_sqlalchemy import (
    TransactionRepositorySqlAlchemy,
)
from app.application.ports.inbound.account_use_cases import AccountUseCases
from app.application.ports.inbound.pix_key_use_cases import PixKeyUseCases
from app.application.services.account_service import AccountService
from app.domain.entities.customer import Customer
from app.infrastructure.db import get_db

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


def get_account_service(db: Session = Depends(get_db)) -> AccountUseCases:
    return AccountService(
        account_repo=AccountRepositorySqlAlchemy(db),
        customer_repo=CustomerRepositorySqlAlchemy(db),
        transaction_repo=TransactionRepositorySqlAlchemy(db),
    )


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    body: AccountCreate,
    current: Customer = Depends(get_current_customer),
    service: AccountUseCases = Depends(get_account_service),
) -> AccountRead:
    ensure_admin(current)
    account = service.create(
        customer_id=body.customer_id, agency=body.agency, number=body.number, label=body.label
    )
    return AccountRead.model_validate(account)


@router.get("", response_model=list[AccountRead])
def list_accounts(
    current: Customer = Depends(get_current_customer),
    service: AccountUseCases = Depends(get_account_service),
) -> list[AccountRead]:
    accounts = service.list() if current.role == "ADMIN" else service.list_by_customer(current.id)
    return [AccountRead.model_validate(account) for account in accounts]


@router.get("/{account_id}", response_model=AccountRead)
def get_account(
    account_id: int,
    current: Customer = Depends(get_current_customer),
    service: AccountUseCases = Depends(get_account_service),
) -> AccountRead:
    account = service.get(account_id)
    ensure_account_owner_or_admin(current, account)
    return AccountRead.model_validate(account)


@router.put("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: int,
    body: AccountUpdate,
    current: Customer = Depends(get_current_customer),
    service: AccountUseCases = Depends(get_account_service),
) -> AccountRead:
    ensure_admin(current)
    account = service.update(account_id, agency=body.agency, label=body.label)
    return AccountRead.model_validate(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int,
    current: Customer = Depends(get_current_customer),
    service: AccountUseCases = Depends(get_account_service),
) -> None:
    ensure_admin(current)
    service.delete(account_id)


@router.get("/{account_id}/balance")
def get_account_balance(
    account_id: int,
    current: Customer = Depends(get_current_customer),
    service: AccountUseCases = Depends(get_account_service),
) -> dict[str, int]:
    account = service.get(account_id)
    ensure_account_owner_or_admin(current, account)
    return {"account_id": account.id, "balance_cents": account.balance_cents}


@router.post(
    "/{account_id}/deposit", response_model=TransactionRead, status_code=status.HTTP_201_CREATED
)
def deposit(
    account_id: int,
    body: DepositRequest,
    current: Customer = Depends(get_current_customer),
    service: AccountUseCases = Depends(get_account_service),
) -> TransactionRead:
    account = service.get(account_id)
    ensure_account_owner_or_admin(current, account)
    transaction = service.deposit(account_id, body.amount_cents)
    return TransactionRead.model_validate(
        transaction
    )  # Transforma "dict" em "TransactionRead" para retornar o objeto correto no response_model


@router.post(
    "/{account_id}/withdraw", response_model=TransactionRead, status_code=status.HTTP_201_CREATED
)
def withdraw(
    account_id: int,
    body: WithdrawRequest,
    current: Customer = Depends(get_current_customer),
    service: AccountUseCases = Depends(get_account_service),
) -> TransactionRead:
    account = service.get(account_id)
    ensure_account_owner_or_admin(current, account)
    transaction = service.withdraw(account_id, body.amount_cents)
    return TransactionRead.model_validate(transaction)


@router.get("/{account_id}/transactions", response_model=list[TransactionRead])
def get_account_statement(
    account_id: int,
    current: Customer = Depends(get_current_customer),
    service: AccountUseCases = Depends(get_account_service),
) -> list[TransactionRead]:
    account = service.get(account_id)
    ensure_account_owner_or_admin(current, account)
    return [TransactionRead.model_validate(t) for t in service.get_statement(account_id)]


@router.get("/{account_id}/pix-keys", response_model=list[PixKeyRead])
def list_account_pix_keys(
    account_id: int,
    current: Customer = Depends(get_current_customer),
    account_service: AccountUseCases = Depends(get_account_service),
    pix_key_service: PixKeyUseCases = Depends(get_pix_key_service),
) -> list[PixKeyRead]:
    account = account_service.get(account_id)
    ensure_account_owner_or_admin(current, account)
    return [
        PixKeyRead.model_validate(pix_key)
        for pix_key in pix_key_service.list_by_account(account_id)
    ]
