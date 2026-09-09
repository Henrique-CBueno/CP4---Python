from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.adapters.inbound.api.schemas import AccountCreate, AccountRead, AccountUpdate
from app.adapters.outbound.persistence.account_repository_sqlalchemy import (
    AccountRepositorySqlAlchemy,
)
from app.adapters.outbound.persistence.customer_repository_sqlalchemy import (
    CustomerRepositorySqlAlchemy,
)
from app.application.services.account_service import AccountService
from app.infrastructure.db import get_db

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


def get_account_service(db: Session = Depends(get_db)) -> AccountService:
    return AccountService(
        account_repo=AccountRepositorySqlAlchemy(db),
        customer_repo=CustomerRepositorySqlAlchemy(db),
    )


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    body: AccountCreate, service: AccountService = Depends(get_account_service)
) -> AccountRead:
    account = service.create(
        customer_id=body.customer_id, agency=body.agency, number=body.number, label=body.label
    )
    return AccountRead.model_validate(account)


@router.get("", response_model=list[AccountRead])
def list_accounts(service: AccountService = Depends(get_account_service)) -> list[AccountRead]:
    return [AccountRead.model_validate(account) for account in service.list()]


@router.get("/{account_id}", response_model=AccountRead)
def get_account(
    account_id: int, service: AccountService = Depends(get_account_service)
) -> AccountRead:
    return AccountRead.model_validate(service.get(account_id))


@router.put("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: int,
    body: AccountUpdate,
    service: AccountService = Depends(get_account_service),
) -> AccountRead:
    account = service.update(account_id, agency=body.agency, label=body.label)
    return AccountRead.model_validate(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int, service: AccountService = Depends(get_account_service)
) -> None:
    service.delete(account_id)
