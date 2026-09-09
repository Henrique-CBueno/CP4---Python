from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain import exceptions as exc

_STATUS_BY_EXCEPTION: dict[type[Exception], int] = {
    exc.CustomerNotFoundError: 404,
    exc.AccountNotFoundError: 404,
    exc.PixKeyNotFoundError: 404,
    exc.DuplicateEmailError: 409,
    exc.DuplicateCpfError: 409,
    exc.DuplicatePixKeyError: 409,
    exc.DuplicateAccountNumberError: 409,
    exc.CustomerHasAccountsError: 409,
    exc.AccountHasDependenciesError: 409,
    exc.InvalidCpfError: 422,
    exc.InvalidPixKeyError: 422,
    exc.InvalidAmountError: 400,
    exc.InsufficientBalanceError: 400,
    exc.SameAccountTransferError: 400,
    exc.InvalidTransactionShapeError: 400,
    exc.NotAuthenticatedError: 401,
    exc.InvalidCredentialsError: 401,
    exc.ForbiddenError: 403,
}


def _make_handler(status_code: int):
    async def handler(request: Request, exc_instance: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(exc_instance)})

    return handler


def register_exception_handlers(app: FastAPI) -> None:
    for exception_type, status_code in _STATUS_BY_EXCEPTION.items():
        app.add_exception_handler(exception_type, _make_handler(status_code))
