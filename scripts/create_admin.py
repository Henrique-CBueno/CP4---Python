"""Cria o primeiro usuário administrador, direto no repositório (sem passar
pela API, que exige estar autenticado como admin para criar clientes)."""

import argparse

from app.adapters.outbound.persistence.customer_repository_sqlalchemy import (
    CustomerRepositorySqlAlchemy,
)
from app.domain.entities.customer import Customer
from app.domain.password_hashing import hash_password
from app.infrastructure.db import SessionLocal, init_db

DEFAULT_NAME = "Administrador"
DEFAULT_EMAIL = "admin@example.com"
DEFAULT_CPF = "52998224725"
DEFAULT_PASSWORD = "admin123"


def create_admin(name: str, email: str, cpf: str, password: str) -> None:
    init_db()
    with SessionLocal() as session:
        repo = CustomerRepositorySqlAlchemy(session)
        if repo.get_by_email(email) is not None:
            print(f"Já existe um cliente com o email {email}; nada foi criado.")
            return

        admin = Customer(
            id=None,
            name=name,
            email=email,
            cpf=cpf,
            password_hash=hash_password(password),
            role="ADMIN",
        )
        repo.add(admin)
        session.commit()
        print(f"Admin criado: {email} / senha: {password}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cria o usuário administrador inicial.")
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--email", default=DEFAULT_EMAIL)
    parser.add_argument("--cpf", default=DEFAULT_CPF)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    args = parser.parse_args()

    create_admin(args.name, args.email, args.cpf, args.password)
