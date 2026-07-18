from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.domain.exceptions import InvalidTokenError
from app.infrastructure.security.jwt_token_issuer import JwtTokenIssuer
from config.settings import settings


@pytest.fixture
def issuer():
    return JwtTokenIssuer()


def test_issue_returns_non_empty_string(issuer):
    token = issuer.issue(uuid4())
    assert isinstance(token, str)
    assert token


def test_token_contains_user_uuid_in_subject(issuer):
    user_uuid = uuid4()
    token = issuer.issue(user_uuid)
    payload = jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
    assert payload['sub'] == str(user_uuid)


def test_token_contains_expiration(issuer):
    token = issuer.issue(uuid4())
    payload = jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
    assert 'exp' in payload


def test_token_is_signed_with_secret(issuer):
    token = issuer.issue(uuid4())
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(
            token,
            '78u5Z6WzExqNMctESx2B/XlWv+tUPz9EFYla50+7H3U=',
            algorithms=[settings.jwt_algorithm],
        )


def test_decode_returns_the_issued_user_uuid(issuer):
    user_uuid = uuid4()
    token = issuer.issue(user_uuid)
    assert issuer.decode(token) == user_uuid


def test_decode_raises_on_malformed_token(issuer):
    with pytest.raises(InvalidTokenError):
        issuer.decode('not-a-jwt')


def test_decode_raises_on_expired_token(issuer):
    expired_token = jwt.encode(
        {'sub': str(uuid4()), 'exp': datetime.now(UTC) - timedelta(minutes=1)},
        key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError):
        issuer.decode(expired_token)


def test_decode_raises_on_wrong_signature(issuer):
    token = jwt.encode(
        {'sub': str(uuid4()), 'exp': datetime.now(UTC) + timedelta(minutes=5)},
        key='a-completely-different-secret-key-value',
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError):
        issuer.decode(token)
