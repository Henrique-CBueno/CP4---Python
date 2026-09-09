from app.domain.password_hashing import hash_password, verify_password


def test_verify_password_with_correct_password():
    hashed = hash_password("Password123")
    assert verify_password("Password123", hashed) is True


def test_verify_password_with_wrong_password():
    hashed = hash_password("Password123")
    assert verify_password("wrong-password", hashed) is False


def test_hash_password_uses_random_salt():
    first = hash_password("Password123")
    second = hash_password("Password123")
    assert first != second


def test_verify_password_with_malformed_hash_returns_false():
    assert verify_password("Password123", "not-a-valid-hash") is False
