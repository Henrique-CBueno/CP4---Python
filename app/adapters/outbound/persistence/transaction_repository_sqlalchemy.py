from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.adapters.outbound.persistence.models import Transaction as TransactionModel
from app.domain.entities.transaction import Transaction


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
        model = TransactionModel(
            source_account_id=source_account_id,
            destination_account_id=destination_account_id,
            type=transaction_type,
            amount_cents=amount_cents,
            description=description,
        )
        self._session.add(model)
        self._session.flush()
        return self._to_domain(model)

    def list_by_account(self, account_id: int) -> list[Transaction]:
        stmt = (
            select(TransactionModel)
            .where(
                or_(
                    TransactionModel.source_account_id == account_id,
                    TransactionModel.destination_account_id == account_id,
                )
            )
            .order_by(TransactionModel.created_at.desc())
        )
        return [self._to_domain(model) for model in self._session.scalars(stmt).all()]

    @staticmethod
    def _to_domain(model: TransactionModel) -> Transaction:
        return Transaction(
            id=model.id,
            source_account_id=model.source_account_id,
            destination_account_id=model.destination_account_id,
            type=model.type,
            amount_cents=model.amount_cents,
            description=model.description,
            created_at=model.created_at,
        )
