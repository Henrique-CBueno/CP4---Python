from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.adapters.inbound.api.account_controller import router as account_router
from app.adapters.inbound.api.auth_controller import router as auth_router
from app.adapters.inbound.api.customer_controller import router as customer_router
from app.adapters.inbound.api.exception_handlers import register_exception_handlers
from app.adapters.inbound.api.pix_key_controller import router as pix_key_router
from app.adapters.inbound.api.pix_transfer_controller import router as pix_transfer_router
from app.adapters.inbound.web.pages import router as web_pages_router
from app.infrastructure.config import BASE_DIR, SECRET_KEY
from app.infrastructure.db import init_db

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="Banco Digital Acadêmico", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
register_exception_handlers(app)
app.include_router(auth_router)
app.include_router(customer_router)
app.include_router(account_router)
app.include_router(pix_key_router)
app.include_router(pix_transfer_router)
app.include_router(web_pages_router)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import os

    import uvicorn

    from alembic import command
    from alembic.config import Config as AlembicConfig
    from scripts.create_admin import (
        DEFAULT_CPF,
        DEFAULT_EMAIL,
        DEFAULT_NAME,
        DEFAULT_PASSWORD,
        create_admin,
    )

    # Aplica as migrações, garante que o admin inicial existe e só então sobe
    # o servidor — tudo com um único comando (`python -m app.main`). Host,
    # porta e reload são configuráveis por env var para permitir rodar uma
    # instância isolada (ex.: um script de demonstração/E2E) sem colidir
    # com um servidor de desenvolvimento já em execução.
    command.upgrade(AlembicConfig(str(BASE_DIR / "alembic.ini")), "head")
    create_admin(DEFAULT_NAME, DEFAULT_EMAIL, DEFAULT_CPF, DEFAULT_PASSWORD)

    uvicorn.run(
        "app.main:app",
        host=os.environ.get("APP_HOST", "127.0.0.1"),
        port=int(os.environ.get("APP_PORT", "8000")),
        reload=os.environ.get("APP_RELOAD", "true").lower() == "true",
    )
