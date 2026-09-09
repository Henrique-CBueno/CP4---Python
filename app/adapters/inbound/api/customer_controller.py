from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.adapters.inbound.api.account_controller import get_account_service
from app.adapters.inbound.api.auth_dependencies import get_current_customer
from app.adapters.inbound.api.authorization import ensure_admin, ensure_self_or_admin
from app.adapters.inbound.api.schemas import AccountRead, CustomerCreate, CustomerRead, CustomerUpdate
from app.adapters.outbound.persistence.account_repository_sqlalchemy import (
    AccountRepositorySqlAlchemy,
)
from app.adapters.outbound.persistence.customer_repository_sqlalchemy import (
    CustomerRepositorySqlAlchemy,
)
from app.application.services.account_service import AccountService
from app.application.services.customer_service import CustomerService
from app.domain.entities.customer import Customer
from app.infrastructure.db import get_db

router = APIRouter(prefix="/api/customers", tags=["customers"])


def get_customer_service(db: Session = Depends(get_db)) -> CustomerService:
    return CustomerService(
        customer_repo=CustomerRepositorySqlAlchemy(db),
        account_repo=AccountRepositorySqlAlchemy(db),
    )


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(
    body: CustomerCreate,
    current: Customer = Depends(get_current_customer),
    service: CustomerService = Depends(get_customer_service),
) -> CustomerRead:
    ensure_admin(current)
    customer = service.create(
        name=body.name, email=body.email, cpf=body.cpf, password=body.password, role=body.role.value
    )
    return CustomerRead.model_validate(customer)


@router.get("", response_model=list[CustomerRead])
def list_customers(
    current: Customer = Depends(get_current_customer),
    service: CustomerService = Depends(get_customer_service),
) -> list[CustomerRead]:
    ensure_admin(current)
    return [CustomerRead.model_validate(customer) for customer in service.list()]


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(
    customer_id: int,
    current: Customer = Depends(get_current_customer),
    service: CustomerService = Depends(get_customer_service),
) -> CustomerRead:
    ensure_self_or_admin(current, customer_id)
    return CustomerRead.model_validate(service.get(customer_id))


@router.put("/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int,
    body: CustomerUpdate,
    current: Customer = Depends(get_current_customer),
    service: CustomerService = Depends(get_customer_service),
) -> CustomerRead:
    ensure_self_or_admin(current, customer_id)
    customer = service.update(customer_id, name=body.name, email=body.email)
    return CustomerRead.model_validate(customer)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: int,
    current: Customer = Depends(get_current_customer),
    service: CustomerService = Depends(get_customer_service),
) -> None:
    ensure_admin(current)
    service.delete(customer_id)


@router.get("/{customer_id}/accounts", response_model=list[AccountRead])
def list_customer_accounts(
    customer_id: int,
    current: Customer = Depends(get_current_customer),
    service: AccountService = Depends(get_account_service),
) -> list[AccountRead]:
    ensure_self_or_admin(current, customer_id)
    return [AccountRead.model_validate(account) for account in service.list_by_customer(customer_id)]
