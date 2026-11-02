import jwt
import pytest

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_hash_password():
    password = "SecurePassword123!"

    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)


def test_wrong_password():
    hashed = hash_password("CorrectPassword123!")

    assert not verify_password(
        "WrongPassword123!",
        hashed,
    )


def test_same_password_produces_different_hashes():
    password = "SecurePassword123!"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash


def test_create_and_decode_access_token():
    user_id = 15

    token = create_access_token(user_id)

    decoded_user_id = decode_access_token(token)

    assert decoded_user_id == user_id


def test_invalid_token():
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("invalid.token.value")
