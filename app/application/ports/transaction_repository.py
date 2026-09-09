from __future__ import annotations

from typing import Protocol

# Transaction não tem entidade de domínio própria (ver 06-architecture.md,
# "hexagonal simplificada, não purista") — o port referencia diretamente o
# modelo de persistência.
from app.adapters.outbound.persistence.models import Transaction


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
