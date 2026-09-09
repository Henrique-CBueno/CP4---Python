"""Exercises the real get_db()/SessionLocal wiring (not the dependency_overrides
used by the `client` fixture) to make sure data survives across two genuinely
separate request-scoped sessions, not just within a single shared session."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.infrastructure.db as db_module
from app.adapters.outbound.persistence import models  # noqa: F401
from app.main import app
from tests.helpers import generate_valid_cpf


@pytest.fixture
def real_db_client(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path}/real.db", connect_args={"check_same_thread": False}
    )
    session_local = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    monkeypatch.setattr(db_module, "engine", engine)
    monkeypatch.setattr(db_module, "SessionLocal", session_local)

    with TestClient(app) as test_client:
        yield test_client


def test_customer_persists_across_separate_requests(real_db_client):
    cpf = generate_valid_cpf("529982247")

    create_response = real_db_client.post(
        "/api/customers", json={"name": "Maria Silva", "email": "maria@example.com", "cpf": cpf}
    )
    assert create_response.status_code == 201
    customer_id = create_response.json()["id"]

    get_response = real_db_client.get(f"/api/customers/{customer_id}")
    assert get_response.status_code == 200
    assert get_response.json()["email"] == "maria@example.com"
