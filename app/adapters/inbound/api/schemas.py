from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr


class PixKeyType(str, Enum):
    CPF = "CPF"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    RANDOM = "RANDOM"


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


class DepositRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount_cents: int


class WithdrawRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount_cents: int


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_account_id: int | None
    destination_account_id: int | None
    type: str
    amount_cents: int
    description: str | None
    created_at: datetime


class PixKeyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: int
    type: PixKeyType
    value: str


class PixKeyUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: PixKeyType | None = None
    value: str | None = None


class PixKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    type: str
    value: str
    created_at: datetime


class PixTransferRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_account_id: int
    pix_key_value: str
    amount_cents: int
