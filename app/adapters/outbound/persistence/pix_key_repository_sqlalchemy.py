from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.outbound.persistence.models import PixKey as PixKeyModel
from app.domain.entities.pix_key import PixKey


class PixKeyRepositorySqlAlchemy:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, pix_key_id: int) -> PixKey | None:
        model = self._session.get(PixKeyModel, pix_key_id)
        return self._to_domain(model) if model else None

    def get_by_value(self, value: str) -> PixKey | None:
        model = self._session.scalar(select(PixKeyModel).where(PixKeyModel.value == value))
        return self._to_domain(model) if model else None

    def list(self) -> list[PixKey]:
        models = self._session.scalars(select(PixKeyModel)).all()
        return [self._to_domain(model) for model in models]

    def list_by_account(self, account_id: int) -> list[PixKey]:
        models = self._session.scalars(
            select(PixKeyModel).where(PixKeyModel.account_id == account_id)
        ).all()
        return [self._to_domain(model) for model in models]

    def add(self, pix_key: PixKey) -> PixKey:
        model = PixKeyModel(account_id=pix_key.account_id, type=pix_key.type, value=pix_key.value)
        self._session.add(model)
        self._session.flush()
        return self._to_domain(model)

    def update(self, pix_key: PixKey) -> PixKey:
        model = self._session.get(PixKeyModel, pix_key.id)
        model.type = pix_key.type
        model.value = pix_key.value
        self._session.flush()
        return self._to_domain(model)

    def delete(self, pix_key: PixKey) -> None:
        model = self._session.get(PixKeyModel, pix_key.id)
        self._session.delete(model)
        self._session.flush()

    @staticmethod
    def _to_domain(model: PixKeyModel) -> PixKey:
        return PixKey(
            id=model.id,
            account_id=model.account_id,
            type=model.type,
            value=model.value,
            created_at=model.created_at,
        )
