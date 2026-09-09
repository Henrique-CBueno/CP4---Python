from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

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
    body: PixTransferRequest, service: PixTransferService = Depends(get_pix_transfer_service)
) -> TransactionRead:
    transaction = service.transfer(
        source_account_id=body.source_account_id,
        pix_key_value=body.pix_key_value,
        amount_cents=body.amount_cents,
    )
    return TransactionRead.model_validate(transaction)
