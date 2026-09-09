class DomainError(Exception):
    """Base class for all domain-level errors."""


class CustomerNotFoundError(DomainError):
    def __init__(self, customer_id: int) -> None:
        super().__init__(f"customer {customer_id} not found")


class AccountNotFoundError(DomainError):
    def __init__(self, account_id: int) -> None:
        super().__init__(f"account {account_id} not found")


class PixKeyNotFoundError(DomainError):
    def __init__(self, identifier: int | str) -> None:
        super().__init__(f"pix key {identifier} not found")


class DuplicateEmailError(DomainError):
    def __init__(self, email: str) -> None:
        super().__init__(f"email {email} already registered")


class DuplicateCpfError(DomainError):
    def __init__(self, cpf: str) -> None:
        super().__init__(f"cpf {cpf} already registered")


class DuplicatePixKeyError(DomainError):
    def __init__(self, value: str) -> None:
        super().__init__(f"pix key value {value} already registered")


class DuplicateAccountNumberError(DomainError):
    def __init__(self, number: str) -> None:
        super().__init__(f"account number {number} already registered")


class InvalidCpfError(DomainError):
    def __init__(self, cpf: str) -> None:
        super().__init__(f"cpf {cpf} is not a valid cpf")


class InvalidAmountError(DomainError):
    def __init__(self, amount_cents: int) -> None:
        super().__init__(f"amount_cents must be greater than zero, got {amount_cents}")


class InsufficientBalanceError(DomainError):
    def __init__(self, account_id: int, amount_cents: int, balance_cents: int) -> None:
        super().__init__(
            f"account {account_id} has insufficient balance ({balance_cents}) "
            f"for an operation of {amount_cents}"
        )


class SameAccountTransferError(DomainError):
    def __init__(self, account_id: int) -> None:
        super().__init__(f"cannot transfer to the same account ({account_id})")


class CustomerHasAccountsError(DomainError):
    def __init__(self, customer_id: int) -> None:
        super().__init__(f"customer {customer_id} has accounts and cannot be deleted")


class AccountHasDependenciesError(DomainError):
    def __init__(self, account_id: int) -> None:
        super().__init__(
            f"account {account_id} has balance, pix keys or transactions "
            "and cannot be deleted"
        )


class InvalidTransactionShapeError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
