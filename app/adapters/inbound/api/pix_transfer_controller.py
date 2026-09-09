from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.adapters.inbound.api.auth_dependencies import get_current_customer
from app.adapters.inbound.api.authorization import ensure_account_owner_or_admin
from app.adapters.inbound.api.schemas import PixTransferRequest, TransactionRead
from app.adapters.outbound.persistence.account_repository_sqlalchemy import (
    AccountRepositorySqlAlchemy,
)
from app.adapters.outbound.persistence.pix_key_repository_sqlalchemy import (
    PixKeyRepositorySqlAlchemy,
)
from app.adapters.outbound.persistence.transaction_repository_sqlalchemy import (
    TransactionRepositorySqlAlchemy,
)
from app.application.services.pix_transfer_service import PixTransferService
from app.domain.entities.customer import Customer
from app.domain.exceptions import AccountNotFoundError
from app.infrastructure.db import get_db

router = APIRouter(prefix="/api/pix", tags=["pix-transfer"])


def get_pix_transfer_service(db: Session = Depends(get_db)) -> PixTransferService:
    return PixTransferService(
        account_repo=AccountRepositorySqlAlchemy(db),
        pix_key_repo=PixKeyRepositorySqlAlchemy(db),
        transaction_repo=TransactionRepositorySqlAlchemy(db),
    )


@router.post("/transfers", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def transfer(
    body: PixTransferRequest,
    current: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
    service: PixTransferService = Depends(get_pix_transfer_service),
) -> TransactionRead:
    source_account = AccountRepositorySqlAlchemy(db).get_by_id(body.source_account_id)
    if source_account is None:
        raise AccountNotFoundError(body.source_account_id)
    ensure_account_owner_or_admin(current, source_account)

    transaction = service.transfer(
        source_account_id=body.source_account_id,
        pix_key_value=body.pix_key_value,
        amount_cents=body.amount_cents,
    )
    return TransactionRead.model_validate(transaction)
