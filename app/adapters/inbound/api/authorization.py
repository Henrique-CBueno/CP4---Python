from app.domain.entities.account import Account
from app.domain.entities.customer import Customer
from app.domain.exceptions import ForbiddenError


def ensure_admin(customer: Customer) -> None:
    if customer.role != "ADMIN":
        raise ForbiddenError("admin role required")


def ensure_self_or_admin(customer: Customer, target_customer_id: int) -> None:
    if customer.role != "ADMIN" and customer.id != target_customer_id:
        raise ForbiddenError("not allowed to access this customer")


def ensure_account_owner_or_admin(customer: Customer, account: Account) -> None:
    if customer.role != "ADMIN" and account.customer_id != customer.id:
        raise ForbiddenError("not allowed to access this account")
