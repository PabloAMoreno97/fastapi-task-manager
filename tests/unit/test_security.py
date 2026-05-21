import pytest
from jose import jwt

from src.core.config import settings
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_is_not_plaintext():
    hashed = hash_password("mysecretpassword")
    assert hashed != "mysecretpassword"


def test_verify_correct_password():
    hashed = hash_password("mysecretpassword")
    assert verify_password("mysecretpassword", hashed) is True


def test_verify_wrong_password_fails():
    hashed = hash_password("mysecretpassword")
    assert verify_password("wrongpassword", hashed) is False


def test_access_token_contains_subject():
    token = create_access_token("user-abc-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-abc-123"


def test_access_token_has_correct_type():
    token = create_access_token("user-abc-123")
    payload = decode_token(token)
    assert payload["type"] == "access"


def test_refresh_token_has_correct_type():
    token = create_refresh_token("user-abc-123")
    payload = decode_token(token)
    assert payload["type"] == "refresh"


def test_invalid_token_returns_empty_dict():
    result = decode_token("not.a.valid.token")
    assert result == {}


def test_tampered_token_returns_empty_dict():
    token = create_access_token("user-abc-123")
    tampered = token[:-5] + "XXXXX"
    assert decode_token(tampered) == {}
