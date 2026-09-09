from app.domain.validators import is_valid_cpf, is_valid_email, is_valid_pix_key
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


def test_pix_key_cpf_uses_cpf_validation():
    assert is_valid_pix_key("CPF", generate_valid_cpf("529982247")) is True
    assert is_valid_pix_key("CPF", "12345678900") is False


def test_pix_key_email_uses_email_validation():
    assert is_valid_pix_key("EMAIL", "maria@example.com") is True
    assert is_valid_pix_key("EMAIL", "maria@") is False


def test_pix_key_phone_accepts_digits_only():
    assert is_valid_pix_key("PHONE", "+5511987654321") is True
    assert is_valid_pix_key("PHONE", "abc") is False


def test_pix_key_random_requires_uuid_format():
    assert is_valid_pix_key("RANDOM", "550e8400-e29b-41d4-a716-446655440000") is True
    assert is_valid_pix_key("RANDOM", "not-a-uuid") is False
