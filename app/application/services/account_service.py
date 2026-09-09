from __future__ import annotations

from app.adapters.outbound.persistence.models import Transaction
from app.application.ports.account_repository import AccountRepository
from app.application.ports.customer_repository import CustomerRepository
from app.application.ports.transaction_repository import TransactionRepository
from app.domain import transaction_rules
from app.domain.entities.account import Account
from app.domain.exceptions import (
    AccountHasDependenciesError,
    AccountNotFoundError,
    CustomerNotFoundError,
    DuplicateAccountNumberError,
)


class AccountService:
    def __init__(
        self,
        account_repo: AccountRepository,
        customer_repo: CustomerRepository,
        transaction_repo: TransactionRepository,
    ) -> None:
        self._account_repo = account_repo
        self._customer_repo = customer_repo
        self._transaction_repo = transaction_repo

    def create(
        self, customer_id: int, agency: str, number: str, label: str | None = None
    ) -> Account:
        if self._customer_repo.get_by_id(customer_id) is None:
            raise CustomerNotFoundError(customer_id)
        if self._account_repo.get_by_number(number) is not None:
            raise DuplicateAccountNumberError(number)

        account = Account(
            id=None,
            customer_id=customer_id,
            agency=agency,
            number=number,
            label=label,
            balance_cents=0,
        )
        return self._account_repo.add(account)

    def list(self) -> list[Account]:
        return self._account_repo.list()

    def list_by_customer(self, customer_id: int) -> list[Account]:
        if self._customer_repo.get_by_id(customer_id) is None:
            raise CustomerNotFoundError(customer_id)
        return self._account_repo.list_by_customer(customer_id)

    def get(self, account_id: int) -> Account:
        account = self._account_repo.get_by_id(account_id)
        if account is None:
            raise AccountNotFoundError(account_id)
        return account

    def update(self, account_id: int, agency: str | None, label: str | None) -> Account:
        account = self.get(account_id)
        if agency is not None:
            account.agency = agency
        if label is not None:
            account.label = label
        return self._account_repo.update(account)

    def delete(self, account_id: int) -> None:
        account = self.get(account_id)
        has_dependencies = (
            account.balance_cents != 0
            or self._account_repo.has_pix_keys(account_id)
            or self._account_repo.has_transactions(account_id)
        )
        if has_dependencies:
            raise AccountHasDependenciesError(account_id)
        self._account_repo.delete(account)

    def deposit(self, account_id: int, amount_cents: int) -> Transaction:
        account = self.get(account_id)
        account.deposit(amount_cents)
        self._account_repo.update(account)
        transaction_rules.validate_transaction_shape("DEPOSIT", None, account.id)
        return self._transaction_repo.add(
            source_account_id=None,
            destination_account_id=account.id,
            transaction_type="DEPOSIT",
            amount_cents=amount_cents,
        )

    def withdraw(self, account_id: int, amount_cents: int) -> Transaction:
        account = self.get(account_id)
        account.withdraw(amount_cents)
        self._account_repo.update(account)
        transaction_rules.validate_transaction_shape("WITHDRAW", account.id, None)
        return self._transaction_repo.add(
            source_account_id=account.id,
            destination_account_id=None,
            transaction_type="WITHDRAW",
            amount_cents=amount_cents,
        )
