from __future__ import annotations

from app.application.ports.account_repository import AccountRepository
from app.application.ports.pix_key_repository import PixKeyRepository
from app.domain import validators
from app.domain.entities.pix_key import PixKey
from app.domain.exceptions import (
    AccountNotFoundError,
    DuplicatePixKeyError,
    InvalidPixKeyError,
    PixKeyNotFoundError,
)


class PixKeyService:
    def __init__(self, pix_key_repo: PixKeyRepository, account_repo: AccountRepository) -> None:
        self._pix_key_repo = pix_key_repo
        self._account_repo = account_repo

    def create(self, account_id: int, key_type: str, value: str) -> PixKey:
        if self._account_repo.get_by_id(account_id) is None:
            raise AccountNotFoundError(account_id)
        if not validators.is_valid_pix_key(key_type, value):
            raise InvalidPixKeyError(key_type, value)
        if self._pix_key_repo.get_by_value(value) is not None:
            raise DuplicatePixKeyError(value)

        pix_key = PixKey(id=None, account_id=account_id, type=key_type, value=value)
        return self._pix_key_repo.add(pix_key)

    def list(self) -> list[PixKey]:
        return self._pix_key_repo.list()

    def list_by_account(self, account_id: int) -> list[PixKey]:
        if self._account_repo.get_by_id(account_id) is None:
            raise AccountNotFoundError(account_id)
        return self._pix_key_repo.list_by_account(account_id)

    def get(self, pix_key_id: int) -> PixKey:
        pix_key = self._pix_key_repo.get_by_id(pix_key_id)
        if pix_key is None:
            raise PixKeyNotFoundError(pix_key_id)
        return pix_key

    def update(self, pix_key_id: int, key_type: str | None, value: str | None) -> PixKey:
        pix_key = self.get(pix_key_id)
        new_type = key_type if key_type is not None else pix_key.type
        new_value = value if value is not None else pix_key.value

        if not validators.is_valid_pix_key(new_type, new_value):
            raise InvalidPixKeyError(new_type, new_value)

        if new_value != pix_key.value:
            existing = self._pix_key_repo.get_by_value(new_value)
            if existing is not None and existing.id != pix_key_id:
                raise DuplicatePixKeyError(new_value)

        pix_key.type = new_type
        pix_key.value = new_value
        return self._pix_key_repo.update(pix_key)

    def delete(self, pix_key_id: int) -> None:
        pix_key = self.get(pix_key_id)
        self._pix_key_repo.delete(pix_key)
