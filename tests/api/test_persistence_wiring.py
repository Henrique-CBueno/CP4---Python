"""Exercises the real get_db()/SessionLocal wiring (not the dependency_overrides
used by the `client` fixture) to make sure data survives across two genuinely
separate request-scoped sessions, not just within a single shared session."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.infrastructure.db as db_module
from app.adapters.outbound.persistence import models  # noqa: F401
from app.adapters.outbound.persistence.customer_repository_sqlalchemy import (
    CustomerRepositorySqlAlchemy,
)
from app.domain.entities.customer import Customer
from app.domain.password_hashing import hash_password
from app.main import app
from tests.helpers import generate_valid_cpf

ADMIN_EMAIL = "admin-real@example.com"
ADMIN_PASSWORD = "AdminPassword123"


@pytest.fixture
def real_db_client(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path}/real.db", connect_args={"check_same_thread": False}
    )
    session_local = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    monkeypatch.setattr(db_module, "engine", engine)
    monkeypatch.setattr(db_module, "SessionLocal", session_local)

    with TestClient(app) as test_client:
        with session_local() as session:
            CustomerRepositorySqlAlchemy(session).add(
                Customer(
                    id=None,
                    name="Admin",
                    email=ADMIN_EMAIL,
                    cpf=generate_valid_cpf("000000001"),
                    password_hash=hash_password(ADMIN_PASSWORD),
                    role="ADMIN",
                )
            )
            session.commit()

        login_response = test_client.post(
            "/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert login_response.status_code == 200

        yield test_client


def test_customer_persists_across_separate_requests(real_db_client):
    cpf = generate_valid_cpf("529982247")

    create_response = real_db_client.post(
        "/api/customers",
        json={
            "name": "Maria Silva",
            "email": "maria@example.com",
            "cpf": cpf,
            "password": "Password123",
        },
    )
    assert create_response.status_code == 201
    customer_id = create_response.json()["id"]

    get_response = real_db_client.get(f"/api/customers/{customer_id}")
    assert get_response.status_code == 200
    assert get_response.json()["email"] == "maria@example.com"
