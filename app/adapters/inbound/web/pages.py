from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.adapters.outbound.persistence.customer_repository_sqlalchemy import (
    CustomerRepositorySqlAlchemy,
)
from app.domain.entities.customer import Customer
from app.infrastructure.db import get_db

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()


def _current_customer(request: Request, db: Session) -> Customer | None:
    customer_id = request.session.get("customer_id")
    if customer_id is None:
        return None
    return CustomerRepositorySqlAlchemy(db).get_by_id(customer_id)


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {})


@router.get("/")
def dashboard_page(request: Request, db: Session = Depends(get_db)):
    if _current_customer(request, db) is None:
        return RedirectResponse("/login")
    return templates.TemplateResponse(request, "dashboard.html", {})


@router.get("/customers")
def customers_page(request: Request, db: Session = Depends(get_db)):
    customer = _current_customer(request, db)
    if customer is None:
        return RedirectResponse("/login")
    if customer.role != "ADMIN":
        return RedirectResponse("/accounts")
    return templates.TemplateResponse(request, "customers.html", {})


@router.get("/accounts")
def accounts_page(request: Request, db: Session = Depends(get_db)):
    if _current_customer(request, db) is None:
        return RedirectResponse("/login")
    return templates.TemplateResponse(request, "accounts.html", {})


@router.get("/accounts/{account_id}")
def account_detail_page(request: Request, account_id: int, db: Session = Depends(get_db)):
    if _current_customer(request, db) is None:
        return RedirectResponse("/login")
    return templates.TemplateResponse(request, "account_detail.html", {"account_id": account_id})


@router.get("/pix/transfer")
def pix_transfer_page(request: Request, db: Session = Depends(get_db)):
    if _current_customer(request, db) is None:
        return RedirectResponse("/login")
    return templates.TemplateResponse(request, "pix_transfer.html", {})
