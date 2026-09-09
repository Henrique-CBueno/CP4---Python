from dataclasses import dataclass
from datetime import datetime


@dataclass
class Account:
    id: int | None
    customer_id: int
    agency: str
    number: str
    label: str | None = None
    balance_cents: int = 0
    created_at: datetime | None = None
