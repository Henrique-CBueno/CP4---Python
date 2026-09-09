from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.adapters.outbound.persistence.customer_repository_sqlalchemy import (
    CustomerRepositorySqlAlchemy,
)
from app.domain.entities.customer import Customer
from app.domain.exceptions import NotAuthenticatedError
from app.infrastructure.db import get_db


def get_current_customer(request: Request, db: Session = Depends(get_db)) -> Customer:
    customer_id = request.session.get("customer_id")
    if customer_id is None:
        raise NotAuthenticatedError()

    customer = CustomerRepositorySqlAlchemy(db).get_by_id(customer_id)
    if customer is None:
        raise NotAuthenticatedError()

    return customer
