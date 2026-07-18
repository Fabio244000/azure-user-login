from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.application.use_cases.logout_user import LogoutUserUseCase
from app.domain.exceptions import InvalidTokenError
from app.domain.ports.output.token_issuer_port import TokenIssuerPort


@pytest.fixture
def token_issuer() -> TokenIssuerPort:
    issuer = Mock(spec=TokenIssuerPort)
    issuer.decode.return_value = uuid4()
    return issuer


@pytest.fixture
def use_case(token_issuer: TokenIssuerPort) -> LogoutUserUseCase:
    return LogoutUserUseCase(token_issuer)


class TestLogoutUserSuccess:
    async def test_decodes_the_token(
        self, use_case: LogoutUserUseCase, token_issuer: TokenIssuerPort
    ) -> None:
        await use_case.execute('a-valid-token')
        token_issuer.decode.assert_called_once_with('a-valid-token')


class TestLogoutUserFailure:
    async def test_raises_on_invalid_token(
        self, use_case: LogoutUserUseCase, token_issuer: TokenIssuerPort
    ) -> None:
        token_issuer.decode.side_effect = InvalidTokenError('invalid or expired token.')
        with pytest.raises(InvalidTokenError):
            await use_case.execute('a-bad-token')
