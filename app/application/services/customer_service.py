from app.application.ports.account_repository import AccountRepository
from app.application.ports.customer_repository import CustomerRepository
from app.domain import validators
from app.domain.entities.customer import Customer
from app.domain.exceptions import (
    CustomerHasAccountsError,
    CustomerNotFoundError,
    DuplicateCpfError,
    DuplicateEmailError,
    InvalidCpfError,
)


class CustomerService:
    def __init__(self, customer_repo: CustomerRepository, account_repo: AccountRepository) -> None:
        self._customer_repo = customer_repo
        self._account_repo = account_repo

    def create(self, name: str, email: str, cpf: str) -> Customer:
        if not validators.is_valid_cpf(cpf):
            raise InvalidCpfError(cpf)
        if self._customer_repo.get_by_email(email) is not None:
            raise DuplicateEmailError(email)
        if self._customer_repo.get_by_cpf(cpf) is not None:
            raise DuplicateCpfError(cpf)

        customer = Customer(id=None, name=name, email=email, cpf=cpf)
        return self._customer_repo.add(customer)

    def list(self) -> list[Customer]:
        return self._customer_repo.list()

    def get(self, customer_id: int) -> Customer:
        customer = self._customer_repo.get_by_id(customer_id)
        if customer is None:
            raise CustomerNotFoundError(customer_id)
        return customer

    def update(self, customer_id: int, name: str | None, email: str | None) -> Customer:
        customer = self.get(customer_id)

        if email is not None and email != customer.email:
            existing = self._customer_repo.get_by_email(email)
            if existing is not None and existing.id != customer_id:
                raise DuplicateEmailError(email)
            customer.email = email

        if name is not None:
            customer.name = name

        return self._customer_repo.update(customer)

    def delete(self, customer_id: int) -> None:
        customer = self.get(customer_id)
        if self._account_repo.list_by_customer(customer_id):
            raise CustomerHasAccountsError(customer_id)
        self._customer_repo.delete(customer)
