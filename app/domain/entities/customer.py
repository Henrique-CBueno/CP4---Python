from dataclasses import dataclass
from datetime import datetime


@dataclass
class Customer:
    id: int | None
    name: str
    email: str
    cpf: str
    password_hash: str
    role: str = "CUSTOMER"
    created_at: datetime | None = None
