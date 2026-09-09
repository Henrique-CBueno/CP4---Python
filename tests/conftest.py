import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.adapters.outbound.persistence import models  # noqa: F401
from app.adapters.outbound.persistence.customer_repository_sqlalchemy import (
    CustomerRepositorySqlAlchemy,
)
from app.domain.entities.customer import Customer
from app.domain.password_hashing import hash_password
from app.infrastructure.db import Base, get_db
from app.main import app
from tests.helpers import generate_valid_cpf

ADMIN_EMAIL = "admin-test@example.com"
ADMIN_PASSWORD = "AdminPassword123"


@pytest.fixture
def db_session(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path}/test.db", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def anonymous_client(db_session):
    """TestClient sem sessão de login — para testar autenticação em si."""

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def client(db_session, anonymous_client):
    """TestClient já logado como admin — a maioria dos testes existentes
    assume acesso total, então este é o fixture padrão. Testes de
    autorização específicos usam `anonymous_client` e criam/logam outros
    clientes explicitamente."""

    CustomerRepositorySqlAlchemy(db_session).add(
        Customer(
            id=None,
            name="Admin de Teste",
            email=ADMIN_EMAIL,
            cpf=generate_valid_cpf("000000001"),
            password_hash=hash_password(ADMIN_PASSWORD),
            role="ADMIN",
        )
    )
    db_session.commit()

    response = anonymous_client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200

    return anonymous_client
