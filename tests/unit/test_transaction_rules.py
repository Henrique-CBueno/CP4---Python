import pytest

from app.domain.exceptions import InvalidTransactionShapeError
from app.domain.transaction_rules import validate_transaction_shape


def test_deposit_requires_only_destination():
    validate_transaction_shape("DEPOSIT", None, 1)


def test_deposit_with_source_is_invalid():
    with pytest.raises(InvalidTransactionShapeError):
        validate_transaction_shape("DEPOSIT", 1, 1)


def test_withdraw_requires_only_source():
    validate_transaction_shape("WITHDRAW", 1, None)


def test_withdraw_with_destination_is_invalid():
    with pytest.raises(InvalidTransactionShapeError):
        validate_transaction_shape("WITHDRAW", 1, 2)


def test_pix_transfer_requires_both_accounts():
    validate_transaction_shape("PIX_TRANSFER", 1, 2)


def test_pix_transfer_missing_source_is_invalid():
    with pytest.raises(InvalidTransactionShapeError):
        validate_transaction_shape("PIX_TRANSFER", None, 2)


def test_pix_transfer_same_account_is_invalid():
    with pytest.raises(InvalidTransactionShapeError):
        validate_transaction_shape("PIX_TRANSFER", 1, 1)


def test_unknown_type_is_invalid():
    with pytest.raises(InvalidTransactionShapeError):
        validate_transaction_shape("REFUND", 1, 2)
