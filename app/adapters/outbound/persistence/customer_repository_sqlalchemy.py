from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.outbound.persistence.models import Customer as CustomerModel
from app.domain.entities.customer import Customer


class CustomerRepositorySqlAlchemy:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, customer_id: int) -> Customer | None:
        model = self._session.get(CustomerModel, customer_id)
        return self._to_domain(model) if model else None

    def list(self) -> list[Customer]:
        models = self._session.scalars(select(CustomerModel)).all()
        return [self._to_domain(model) for model in models]

    def get_by_email(self, email: str) -> Customer | None:
        model = self._session.scalar(select(CustomerModel).where(CustomerModel.email == email))
        return self._to_domain(model) if model else None

    def get_by_cpf(self, cpf: str) -> Customer | None:
        model = self._session.scalar(select(CustomerModel).where(CustomerModel.cpf == cpf))
        return self._to_domain(model) if model else None

    def add(self, customer: Customer) -> Customer:
        model = CustomerModel(
            name=customer.name,
            email=customer.email,
            cpf=customer.cpf,
            password_hash=customer.password_hash,
            role=customer.role,
        )
        self._session.add(model)
        self._session.flush()
        return self._to_domain(model)

    def update(self, customer: Customer) -> Customer:
        model = self._session.get(CustomerModel, customer.id)
        model.name = customer.name
        model.email = customer.email
        self._session.flush()
        return self._to_domain(model)

    def delete(self, customer: Customer) -> None:
        model = self._session.get(CustomerModel, customer.id)
        self._session.delete(model)
        self._session.flush()

    @staticmethod
    def _to_domain(model: CustomerModel) -> Customer:
        return Customer(
            id=model.id,
            name=model.name,
            email=model.email,
            cpf=model.cpf,
            password_hash=model.password_hash,
            role=model.role,
            created_at=model.created_at,
        )
