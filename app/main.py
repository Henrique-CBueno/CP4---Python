from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.adapters.inbound.api.account_controller import router as account_router
from app.adapters.inbound.api.customer_controller import router as customer_router
from app.adapters.inbound.api.exception_handlers import register_exception_handlers
from app.adapters.inbound.web.pages import router as web_pages_router
from app.infrastructure.db import init_db

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="Banco Digital Acadêmico", lifespan=lifespan)

register_exception_handlers(app)
app.include_router(customer_router)
app.include_router(account_router)
app.include_router(web_pages_router)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
