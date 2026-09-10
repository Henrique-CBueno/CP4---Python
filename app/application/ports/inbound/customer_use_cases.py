from __future__ import annotations

from typing import Protocol

from app.domain.entities.customer import Customer


class CustomerUseCases(Protocol):
    def create(
        self, name: str, email: str, cpf: str, password: str, role: str = "CUSTOMER"
    ) -> Customer: ...

    def authenticate(self, email: str, password: str) -> Customer: ...

    def list(self) -> list[Customer]: ...

    def get(self, customer_id: int) -> Customer: ...

    def update(self, customer_id: int, name: str | None, email: str | None) -> Customer: ...

    def delete(self, customer_id: int) -> None: ...
