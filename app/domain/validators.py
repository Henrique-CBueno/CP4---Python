import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email))


def _cpf_check_digit(digits: str, weight_start: int) -> str:
    total = sum(int(digit) * weight for digit, weight in zip(digits, range(weight_start, 1, -1)))
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
