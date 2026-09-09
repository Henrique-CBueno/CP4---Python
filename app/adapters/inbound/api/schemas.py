from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class CustomerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    email: EmailStr
    cpf: str


class CustomerUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    email: EmailStr | None = None


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    cpf: str
    created_at: datetime


class AccountCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: int
    agency: str
    number: str
    label: str | None = None


class AccountUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agency: str | None = None
    label: str | None = None


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    agency: str
    number: str
    label: str | None
    balance_cents: int
    created_at: datetime
