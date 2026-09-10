from __future__ import annotations

from typing import Protocol

from app.domain.entities.transaction import Transaction


class PixTransferUseCases(Protocol):
    def transfer(
        self, source_account_id: int, pix_key_value: str, amount_cents: int
    ) -> Transaction: ...
