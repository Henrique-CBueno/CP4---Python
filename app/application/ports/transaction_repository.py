from __future__ import annotations

from typing import Protocol

from app.domain.entities.transaction import Transaction


class TransactionRepository(Protocol):
    def add(
        self,
        source_account_id: int | None,
        destination_account_id: int | None,
        transaction_type: str,
        amount_cents: int,
        description: str | None = None,
    ) -> Transaction: ...

    def list_by_account(self, account_id: int) -> list[Transaction]: ...
