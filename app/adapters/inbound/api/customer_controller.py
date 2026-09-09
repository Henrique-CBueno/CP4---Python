from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.adapters.inbound.api.schemas import CustomerCreate, CustomerRead, CustomerUpdate
from app.adapters.outbound.persistence.customer_repository_sqlalchemy import (
    CustomerRepositorySqlAlchemy,
)
from app.application.services.customer_service import CustomerService
from app.infrastructure.db import get_db

router = APIRouter(prefix="/api/customers", tags=["customers"])


def get_customer_service(db: Session = Depends(get_db)) -> CustomerService:
    return CustomerService(customer_repo=CustomerRepositorySqlAlchemy(db))


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(
    body: CustomerCreate, service: CustomerService = Depends(get_customer_service)
) -> CustomerRead:
    customer = service.create(name=body.name, email=body.email, cpf=body.cpf)
    return CustomerRead.model_validate(customer)


@router.get("", response_model=list[CustomerRead])
def list_customers(
    service: CustomerService = Depends(get_customer_service),
) -> list[CustomerRead]:
    return [CustomerRead.model_validate(customer) for customer in service.list()]


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(
    customer_id: int, service: CustomerService = Depends(get_customer_service)
) -> CustomerRead:
    return CustomerRead.model_validate(service.get(customer_id))


@router.put("/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int,
    body: CustomerUpdate,
    service: CustomerService = Depends(get_customer_service),
) -> CustomerRead:
    customer = service.update(customer_id, name=body.name, email=body.email)
    return CustomerRead.model_validate(customer)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: int, service: CustomerService = Depends(get_customer_service)
) -> None:
    service.delete(customer_id)
