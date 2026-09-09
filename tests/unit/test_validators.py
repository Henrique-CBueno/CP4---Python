from app.domain.validators import is_valid_cpf, is_valid_email
from tests.helpers import generate_valid_cpf


def test_valid_cpf_is_accepted():
    assert is_valid_cpf(generate_valid_cpf("529982247")) is True


def test_cpf_with_wrong_check_digit_is_rejected():
    valid = generate_valid_cpf("529982247")
    tampered = valid[:-1] + ("0" if valid[-1] != "0" else "1")
    assert is_valid_cpf(tampered) is False


def test_cpf_with_wrong_length_is_rejected():
    assert is_valid_cpf("123456789") is False


def test_cpf_with_all_repeated_digits_is_rejected():
    assert is_valid_cpf("11111111111") is False


def test_valid_email_is_accepted():
    assert is_valid_email("maria@example.com") is True


def test_email_without_domain_is_rejected():
    assert is_valid_email("maria@") is False
