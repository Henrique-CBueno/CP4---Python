from dataclasses import dataclass
from datetime import datetime


@dataclass
class PixKey:
    id: int | None
    account_id: int
    type: str
    value: str
    created_at: datetime | None = None
