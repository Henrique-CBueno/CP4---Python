from app.domain.exceptions import InvalidTransactionShapeError

# (source_account_id é obrigatório?, destination_account_id é obrigatório?)
_EXPECTED_SHAPE: dict[str, tuple[bool, bool]] = {
    "DEPOSIT": (False, True),
    "WITHDRAW": (True, False),
    "PIX_TRANSFER": (True, True),
}


def validate_transaction_shape(
    transaction_type: str,
    source_account_id: int | None,
    destination_account_id: int | None,
) -> None:
    if transaction_type not in _EXPECTED_SHAPE:
        raise InvalidTransactionShapeError(f"unknown transaction type {transaction_type}")

    source_required, destination_required = _EXPECTED_SHAPE[transaction_type]

    if source_required and source_account_id is None:
        raise InvalidTransactionShapeError(f"{transaction_type} requires a source_account_id")
    if not source_required and source_account_id is not None:
        raise InvalidTransactionShapeError(f"{transaction_type} must not have a source_account_id")
    if destination_required and destination_account_id is None:
        raise InvalidTransactionShapeError(f"{transaction_type} requires a destination_account_id")
    if not destination_required and destination_account_id is not None:
        raise InvalidTransactionShapeError(
            f"{transaction_type} must not have a destination_account_id"
        )
    if transaction_type == "PIX_TRANSFER" and source_account_id == destination_account_id:
        raise InvalidTransactionShapeError("PIX_TRANSFER source and destination must differ")
