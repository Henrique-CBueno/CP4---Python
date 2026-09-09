from app.adapters.outbound.persistence.customer_repository_sqlalchemy import (
    CustomerRepositorySqlAlchemy,
)
from app.domain.entities.customer import Customer
from app.domain.password_hashing import hash_password
from tests.helpers import generate_valid_cpf


def _create_customer_directly(
    db_session, email="maria@example.com", password="Password123", role="CUSTOMER"
):
    CustomerRepositorySqlAlchemy(db_session).add(
        Customer(
            id=None,
            name="Maria Silva",
            email=email,
            cpf=generate_valid_cpf("529982247"),
            password_hash=hash_password(password),
            role=role,
        )
    )
    db_session.commit()


def test_login_success(anonymous_client, db_session):
    _create_customer_directly(db_session)

    response = anonymous_client.post(
        "/api/auth/login", json={"email": "maria@example.com", "password": "Password123"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "maria@example.com"


def test_login_wrong_password_returns_401(anonymous_client, db_session):
    _create_customer_directly(db_session)

    response = anonymous_client.post(
        "/api/auth/login", json={"email": "maria@example.com", "password": "wrong-password"}
    )
    assert response.status_code == 401


def test_login_unknown_email_returns_401(anonymous_client):
    response = anonymous_client.post(
        "/api/auth/login", json={"email": "ghost@example.com", "password": "whatever"}
    )
    assert response.status_code == 401


def test_me_without_session_returns_401(anonymous_client):
    response = anonymous_client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_with_session_returns_current_user(anonymous_client, db_session):
    _create_customer_directly(db_session)
    anonymous_client.post(
        "/api/auth/login", json={"email": "maria@example.com", "password": "Password123"}
    )

    response = anonymous_client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "maria@example.com"


def test_logout_clears_session(anonymous_client, db_session):
    _create_customer_directly(db_session)
    anonymous_client.post(
        "/api/auth/login", json={"email": "maria@example.com", "password": "Password123"}
    )

    response = anonymous_client.post("/api/auth/logout")
    assert response.status_code == 204

    response = anonymous_client.get("/api/auth/me")
    assert response.status_code == 401
