from dataclasses import dataclass
from datetime import datetime

from app.domain.exceptions import InsufficientBalanceError, InvalidAmountError


@dataclass
class Account:
    id: int | None
    customer_id: int
    agency: str
    number: str
    label: str | None = None
    balance_cents: int = 0
    created_at: datetime | None = None

    def deposit(self, amount_cents: int) -> None:
        if amount_cents <= 0:
            raise InvalidAmountError(amount_cents)
        self.balance_cents += amount_cents

    def withdraw(self, amount_cents: int) -> None:
        if amount_cents <= 0:
            raise InvalidAmountError(amount_cents)
        if amount_cents > self.balance_cents:
            raise InsufficientBalanceError(self.id, amount_cents, self.balance_cents)
        self.balance_cents -= amount_cents
