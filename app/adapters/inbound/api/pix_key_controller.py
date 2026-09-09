from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.adapters.inbound.api.schemas import PixKeyCreate, PixKeyRead, PixKeyUpdate
from app.adapters.outbound.persistence.account_repository_sqlalchemy import (
    AccountRepositorySqlAlchemy,
)
from app.adapters.outbound.persistence.pix_key_repository_sqlalchemy import (
    PixKeyRepositorySqlAlchemy,
)
from app.application.services.pix_key_service import PixKeyService
from app.infrastructure.db import get_db

router = APIRouter(prefix="/api/pix-keys", tags=["pix-keys"])


def get_pix_key_service(db: Session = Depends(get_db)) -> PixKeyService:
    return PixKeyService(
        pix_key_repo=PixKeyRepositorySqlAlchemy(db),
        account_repo=AccountRepositorySqlAlchemy(db),
    )


@router.post("", response_model=PixKeyRead, status_code=status.HTTP_201_CREATED)
def create_pix_key(
    body: PixKeyCreate, service: PixKeyService = Depends(get_pix_key_service)
) -> PixKeyRead:
    pix_key = service.create(account_id=body.account_id, key_type=body.type.value, value=body.value)
    return PixKeyRead.model_validate(pix_key)


@router.get("", response_model=list[PixKeyRead])
def list_pix_keys(service: PixKeyService = Depends(get_pix_key_service)) -> list[PixKeyRead]:
    return [PixKeyRead.model_validate(pix_key) for pix_key in service.list()]


@router.get("/{pix_key_id}", response_model=PixKeyRead)
def get_pix_key(
    pix_key_id: int, service: PixKeyService = Depends(get_pix_key_service)
) -> PixKeyRead:
    return PixKeyRead.model_validate(service.get(pix_key_id))


@router.put("/{pix_key_id}", response_model=PixKeyRead)
def update_pix_key(
    pix_key_id: int,
    body: PixKeyUpdate,
    service: PixKeyService = Depends(get_pix_key_service),
) -> PixKeyRead:
    key_type = body.type.value if body.type is not None else None
    pix_key = service.update(pix_key_id, key_type=key_type, value=body.value)
    return PixKeyRead.model_validate(pix_key)


@router.delete("/{pix_key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pix_key(
    pix_key_id: int, service: PixKeyService = Depends(get_pix_key_service)
) -> None:
    service.delete(pix_key_id)
