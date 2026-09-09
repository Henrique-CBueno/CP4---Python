from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.adapters.inbound.api.auth_dependencies import get_current_customer
from app.adapters.inbound.api.authorization import ensure_account_owner_or_admin, ensure_admin
from app.adapters.inbound.api.schemas import PixKeyCreate, PixKeyRead, PixKeyUpdate
from app.adapters.outbound.persistence.account_repository_sqlalchemy import (
    AccountRepositorySqlAlchemy,
)
from app.adapters.outbound.persistence.pix_key_repository_sqlalchemy import (
    PixKeyRepositorySqlAlchemy,
)
from app.application.services.pix_key_service import PixKeyService
from app.domain.entities.customer import Customer
from app.domain.exceptions import AccountNotFoundError
from app.infrastructure.db import get_db

router = APIRouter(prefix="/api/pix-keys", tags=["pix-keys"])


def get_pix_key_service(db: Session = Depends(get_db)) -> PixKeyService:
    return PixKeyService(
        pix_key_repo=PixKeyRepositorySqlAlchemy(db),
        account_repo=AccountRepositorySqlAlchemy(db),
    )


def _ensure_owns_account(db: Session, current: Customer, account_id: int) -> None:
    account = AccountRepositorySqlAlchemy(db).get_by_id(account_id)
    if account is None:
        raise AccountNotFoundError(account_id)
    ensure_account_owner_or_admin(current, account)


@router.post("", response_model=PixKeyRead, status_code=status.HTTP_201_CREATED)
def create_pix_key(
    body: PixKeyCreate,
    current: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
    service: PixKeyService = Depends(get_pix_key_service),
) -> PixKeyRead:
    _ensure_owns_account(db, current, body.account_id)
    pix_key = service.create(account_id=body.account_id, key_type=body.type.value, value=body.value)
    return PixKeyRead.model_validate(pix_key)


@router.get("", response_model=list[PixKeyRead])
def list_pix_keys(
    current: Customer = Depends(get_current_customer),
    service: PixKeyService = Depends(get_pix_key_service),
) -> list[PixKeyRead]:
    ensure_admin(current)
    return [PixKeyRead.model_validate(pix_key) for pix_key in service.list()]


@router.get("/{pix_key_id}", response_model=PixKeyRead)
def get_pix_key(
    pix_key_id: int,
    current: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
    service: PixKeyService = Depends(get_pix_key_service),
) -> PixKeyRead:
    pix_key = service.get(pix_key_id)
    _ensure_owns_account(db, current, pix_key.account_id)
    return PixKeyRead.model_validate(pix_key)


@router.put("/{pix_key_id}", response_model=PixKeyRead)
def update_pix_key(
    pix_key_id: int,
    body: PixKeyUpdate,
    current: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
    service: PixKeyService = Depends(get_pix_key_service),
) -> PixKeyRead:
    existing = service.get(pix_key_id)
    _ensure_owns_account(db, current, existing.account_id)
    key_type = body.type.value if body.type is not None else None
    pix_key = service.update(pix_key_id, key_type=key_type, value=body.value)
    return PixKeyRead.model_validate(pix_key)


@router.delete("/{pix_key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pix_key(
    pix_key_id: int,
    current: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
    service: PixKeyService = Depends(get_pix_key_service),
) -> None:
    pix_key = service.get(pix_key_id)
    _ensure_owns_account(db, current, pix_key.account_id)
    service.delete(pix_key_id)
