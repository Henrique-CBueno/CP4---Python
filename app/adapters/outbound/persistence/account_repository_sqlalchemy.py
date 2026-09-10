from __future__ import annotations

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.adapters.outbound.persistence.models import Account as AccountModel
from app.adapters.outbound.persistence.models import PixKey as PixKeyModel
from app.adapters.outbound.persistence.models import Transaction as TransactionModel
from app.domain.entities.account import Account


class AccountRepositorySqlAlchemy:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, account_id: int) -> Account | None:
        model = self._session.get(AccountModel, account_id)
        return self._to_domain(model) if model else None

    def get_by_number(self, number: str) -> Account | None:
        model = self._session.scalar(select(AccountModel).where(AccountModel.number == number))
        return self._to_domain(model) if model else None

    def list(self) -> list[Account]:
        models = self._session.scalars(select(AccountModel)).all()
        return [self._to_domain(model) for model in models]

    def list_by_customer(self, customer_id: int) -> list[Account]:
        models = self._session.scalars(
            select(AccountModel).where(AccountModel.customer_id == customer_id)
        ).all()
        return [self._to_domain(model) for model in models]

    def add(self, account: Account) -> Account:
        model = AccountModel(
            customer_id=account.customer_id,
            agency=account.agency,
            number=account.number,
            label=account.label,
        )
        self._session.add(model)
        self._session.flush()
        return self._to_domain(model)

    def update(self, account: Account) -> Account:
        model = self._session.get(AccountModel, account.id)
        model.agency = account.agency
        model.label = account.label
        self._session.flush()
        return self._to_domain(model)

    def delete(self, account: Account) -> None:
        model = self._session.get(AccountModel, account.id)
        self._session.delete(model)
        self._session.flush()

    def has_pix_keys(self, account_id: int) -> bool:
        return bool(
            self._session.scalar(select(exists().where(PixKeyModel.account_id == account_id)))
        )

    def has_transactions(self, account_id: int) -> bool:
        return bool(
            self._session.scalar(
                select(
                    exists().where(
                        (TransactionModel.source_account_id == account_id)
                        | (TransactionModel.destination_account_id == account_id)
                    )
                )
            )
        )

    def _compute_balance(self, account_id: int) -> int:
        credits = self._session.scalar(
            select(func.coalesce(func.sum(TransactionModel.amount_cents), 0)).where(
                TransactionModel.destination_account_id == account_id
            )
        )
        debits = self._session.scalar(
            select(func.coalesce(func.sum(TransactionModel.amount_cents), 0)).where(
                TransactionModel.source_account_id == account_id
            )
        )
        return credits - debits

    def _to_domain(self, model: AccountModel) -> Account:
        return Account(
            id=model.id,
            customer_id=model.customer_id,
            agency=model.agency,
            number=model.number,
            label=model.label,
            balance_cents=self._compute_balance(model.id),
            created_at=model.created_at,
        )
