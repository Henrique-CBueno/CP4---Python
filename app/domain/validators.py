import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^\+?\d{10,15}$")
_RANDOM_KEY_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email))


def is_valid_phone(value: str) -> bool:
    return bool(_PHONE_RE.match(value))


def is_valid_random_key(value: str) -> bool:
    return bool(_RANDOM_KEY_RE.match(value))


def is_valid_pix_key(key_type: str, value: str) -> bool:
    if key_type == "CPF":
        return is_valid_cpf(value)
    if key_type == "EMAIL":
        return is_valid_email(value)
    if key_type == "PHONE":
        return is_valid_phone(value)
    if key_type == "RANDOM":
        return is_valid_random_key(value)
    return False


def _cpf_check_digit(digits: str, weight_start: int) -> str:
    total = sum(
        int(digit) * weight
        for digit, weight in zip(digits, range(weight_start, 1, -1), strict=False)
    )
    remainder = (total * 10) % 11
    return "0" if remainder == 10 else str(remainder)


def is_valid_cpf(cpf: str) -> bool:
    digits = re.sub(r"\D", "", cpf)

    if len(digits) != 11 or digits == digits[0] * 11:
        return False

    first_check_digit = _cpf_check_digit(digits[:9], 10)
    if first_check_digit != digits[9]:
        return False

    second_check_digit = _cpf_check_digit(digits[:10], 11)
    return second_check_digit == digits[10]
