from app.domain.exceptions import InsufficientBalanceError, InvalidAmountError


def validate_deposit(amount_cents: int) -> None:
    if amount_cents <= 0:
        raise InvalidAmountError(amount_cents)


def validate_withdraw(account_id: int, amount_cents: int, current_balance_cents: int) -> None:
    if amount_cents <= 0:
        raise InvalidAmountError(amount_cents)
    if amount_cents > current_balance_cents:
        raise InsufficientBalanceError(account_id, amount_cents, current_balance_cents)
