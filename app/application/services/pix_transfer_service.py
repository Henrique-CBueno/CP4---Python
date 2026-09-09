from __future__ import annotations

from app.adapters.outbound.persistence.models import Transaction
from app.application.ports.account_repository import AccountRepository
from app.application.ports.pix_key_repository import PixKeyRepository
from app.application.ports.transaction_repository import TransactionRepository
from app.domain import transaction_rules
from app.domain.exceptions import (
    AccountNotFoundError,
    InvalidAmountError,
    PixKeyNotFoundError,
    SameAccountTransferError,
)


class PixTransferService:
    def __init__(
        self,
        account_repo: AccountRepository,
        pix_key_repo: PixKeyRepository,
        transaction_repo: TransactionRepository,
    ) -> None:
        self._account_repo = account_repo
        self._pix_key_repo = pix_key_repo
        self._transaction_repo = transaction_repo

    def transfer(
        self, source_account_id: int, pix_key_value: str, amount_cents: int
    ) -> Transaction:
        if amount_cents <= 0:
            raise InvalidAmountError(amount_cents)

        source = self._account_repo.get_by_id(source_account_id)
        if source is None:
            raise AccountNotFoundError(source_account_id)

        pix_key = self._pix_key_repo.get_by_value(pix_key_value)
        if pix_key is None:
            raise PixKeyNotFoundError(pix_key_value)

        destination = self._account_repo.get_by_id(pix_key.account_id)

        if source.id == destination.id:
            raise SameAccountTransferError(source.id)

        source.withdraw(amount_cents)
        destination.deposit(amount_cents)

        self._account_repo.update(source)
        self._account_repo.update(destination)

        transaction_rules.validate_transaction_shape("PIX_TRANSFER", source.id, destination.id)

        return self._transaction_repo.add(
            source_account_id=source.id,
            destination_account_id=destination.id,
            transaction_type="PIX_TRANSFER",
            amount_cents=amount_cents,
        )
