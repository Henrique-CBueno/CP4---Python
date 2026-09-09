from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.adapters.outbound.persistence.models import Transaction


class TransactionRepositorySqlAlchemy:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(
        self,
        source_account_id: int | None,
        destination_account_id: int | None,
        transaction_type: str,
        amount_cents: int,
        description: str | None = None,
    ) -> Transaction:
        model = Transaction(
            source_account_id=source_account_id,
            destination_account_id=destination_account_id,
            type=transaction_type,
            amount_cents=amount_cents,
            description=description,
        )
        self._session.add(model)
        self._session.flush()
        return model

    def list_by_account(self, account_id: int) -> list[Transaction]:
        stmt = (
            select(Transaction)
            .where(
                or_(
                    Transaction.source_account_id == account_id,
                    Transaction.destination_account_id == account_id,
                )
            )
            .order_by(Transaction.created_at.desc())
        )
        return list(self._session.scalars(stmt).all())
