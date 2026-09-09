from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()


@router.get("/customers")
def customers_page(request: Request):
    return templates.TemplateResponse(request, "customers.html", {})


@router.get("/accounts")
def accounts_page(request: Request):
    return templates.TemplateResponse(request, "accounts.html", {})


@router.get("/accounts/{account_id}")
def account_detail_page(request: Request, account_id: int):
    return templates.TemplateResponse(
        request, "account_detail.html", {"account_id": account_id}
    )


@router.get("/pix/transfer")
def pix_transfer_page(request: Request):
    return templates.TemplateResponse(request, "pix_transfer.html", {})
