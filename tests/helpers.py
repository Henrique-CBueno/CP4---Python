def generate_valid_cpf(base_digits: str) -> str:
    """Builds a valid CPF from 9 base digits, computing both check digits."""

    def _check_digit(digits: str, weight_start: int) -> str:
        total = sum(int(d) * w for d, w in zip(digits, range(weight_start, 1, -1)))
        remainder = (total * 10) % 11
        return "0" if remainder == 10 else str(remainder)

    first = _check_digit(base_digits, 10)
    second = _check_digit(base_digits + first, 11)
    return base_digits + first + second
