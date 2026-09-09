from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.adapters.inbound.api.auth_dependencies import get_current_customer
from app.adapters.inbound.api.schemas import CurrentUserRead, LoginRequest
from app.adapters.outbound.persistence.account_repository_sqlalchemy import (
    AccountRepositorySqlAlchemy,
)
from app.adapters.outbound.persistence.customer_repository_sqlalchemy import (
    CustomerRepositorySqlAlchemy,
)
from app.application.services.customer_service import CustomerService
from app.domain.entities.customer import Customer
from app.infrastructure.db import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_customer_service(db: Session = Depends(get_db)) -> CustomerService:
    return CustomerService(
        customer_repo=CustomerRepositorySqlAlchemy(db),
        account_repo=AccountRepositorySqlAlchemy(db),
    )


@router.post("/login", response_model=CurrentUserRead)
def login(
    request: Request,
    body: LoginRequest,
    service: CustomerService = Depends(get_customer_service),
) -> CurrentUserRead:
    customer = service.authenticate(email=body.email, password=body.password)
    request.session["customer_id"] = customer.id
    return CurrentUserRead.model_validate(customer)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request) -> None:
    request.session.clear()


@router.get("/me", response_model=CurrentUserRead)
def me(current: Customer = Depends(get_current_customer)) -> CurrentUserRead:
    return CurrentUserRead.model_validate(current)
