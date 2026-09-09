import pytest

from app.adapters.outbound.persistence import models  # noqa: F401
from app.adapters.outbound.persistence.customer_repository_sqlalchemy import (
    CustomerRepositorySqlAlchemy,
)
from app.application.services.customer_service import CustomerService
from app.domain.exceptions import (
    CustomerNotFoundError,
    DuplicateCpfError,
    DuplicateEmailError,
    InvalidCpfError,
)
from tests.helpers import generate_valid_cpf

VALID_CPF = generate_valid_cpf("529982247")
OTHER_VALID_CPF = generate_valid_cpf("111444777")


def make_service(db_session) -> CustomerService:
    return CustomerService(customer_repo=CustomerRepositorySqlAlchemy(db_session))


def test_create_customer_success(db_session):
    service = make_service(db_session)

    customer = service.create(name="Maria Silva", email="maria@example.com", cpf=VALID_CPF)

    assert customer.id is not None
    assert customer.name == "Maria Silva"
    assert customer.cpf == VALID_CPF


def test_create_customer_invalid_cpf(db_session):
    service = make_service(db_session)

    with pytest.raises(InvalidCpfError):
        service.create(name="Maria Silva", email="maria@example.com", cpf="12345678900")


def test_create_customer_duplicate_email(db_session):
    service = make_service(db_session)
    service.create(name="Maria Silva", email="maria@example.com", cpf=VALID_CPF)

    with pytest.raises(DuplicateEmailError):
        service.create(name="Outro Nome", email="maria@example.com", cpf=OTHER_VALID_CPF)


def test_create_customer_duplicate_cpf(db_session):
    service = make_service(db_session)
    service.create(name="Maria Silva", email="maria@example.com", cpf=VALID_CPF)

    with pytest.raises(DuplicateCpfError):
        service.create(name="Outro Nome", email="outro@example.com", cpf=VALID_CPF)


def test_update_customer_name_and_email(db_session):
    service = make_service(db_session)
    customer = service.create(name="Maria Silva", email="maria@example.com", cpf=VALID_CPF)

    updated = service.update(customer.id, name="Maria S. Silva", email="maria.s@example.com")

    assert updated.name == "Maria S. Silva"
    assert updated.email == "maria.s@example.com"


def test_delete_customer_without_accounts(db_session):
    service = make_service(db_session)
    customer = service.create(name="Maria Silva", email="maria@example.com", cpf=VALID_CPF)

    service.delete(customer.id)

    with pytest.raises(CustomerNotFoundError):
        service.get(customer.id)


def test_get_missing_customer_raises_not_found(db_session):
    service = make_service(db_session)

    with pytest.raises(CustomerNotFoundError):
        service.get(999)
