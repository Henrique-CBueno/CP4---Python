from dataclasses import dataclass
from datetime import datetime


@dataclass
class Transaction:
    """Registro de uma movimentação financeira do domínio."""

    id: int | None
    source_account_id: int | None
    destination_account_id: int | None
    type: str
    amount_cents: int
    description: str | None = None
    created_at: datetime | None = None
