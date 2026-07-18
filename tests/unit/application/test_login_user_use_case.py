from typing import Any
from unittest.mock import Mock

import pytest

from app.application.use_cases.login_user import LoginUserUseCase
from app.domain.entities.user import User
from app.domain.exceptions import InvalidCredentialsError
from app.domain.ports.output.password_hasher_port import PasswordHasherPort
from app.domain.ports.output.token_issuer_port import TokenIssuerPort
from app.domain.ports.output.user_repository_port import UserRepositoryPort


def _existing_user(**overrides: Any) -> User:
    data: dict[str, Any] = {
        'first_name': 'fabio',
        'last_name': 'nunez garcia',
        'cellphone': '+51 987654321',
        'username': 'fabio01',
        'password': 'plainpass1',
        'email': 'fabio@mail.com',
    }
    data.update(overrides)
    user = User(**data)
    if user.password:
        user.password = 'hashed'
    return user


@pytest.fixture
def repository() -> UserRepositoryPort:
    repo = Mock(spec=UserRepositoryPort)
    repo.find_by_username.return_value = _existing_user()
    return repo


@pytest.fixture
def hasher() -> PasswordHasherPort:
    hasher = Mock(spec=PasswordHasherPort)
    hasher.verify.return_value = True
    return hasher


@pytest.fixture
def token_issuer() -> TokenIssuerPort:
    issuer = Mock(spec=TokenIssuerPort)
    issuer.issue.return_value = 'session_token'
    return issuer


@pytest.fixture
def use_case(
    repository: UserRepositoryPort,
    hasher: PasswordHasherPort,
    token_issuer: TokenIssuerPort,
) -> LoginUserUseCase:
    return LoginUserUseCase(repository, hasher, token_issuer)


class TestLoginUserSuccess:
    async def test_returns_user_and_token(self, use_case: LoginUserUseCase) -> None:
        user, token = await use_case.execute(username='fabio01', password='plainpass1')
        assert isinstance(user, User)
        assert token == 'session_token'

    async def test_verifies_password_against_stored_hash(
        self,
        use_case: LoginUserUseCase,
        hasher: PasswordHasherPort,
        repository: UserRepositoryPort,
    ) -> None:
        await use_case.execute(username='fabio01', password='plainpass1')
        hasher.verify.assert_called_once_with('plainpass1', 'hashed')

    async def test_issues_token_for_found_user(
        self, use_case: LoginUserUseCase, token_issuer: TokenIssuerPort
    ) -> None:
        user, _ = await use_case.execute(username='fabio01', password='plainpass1')
        token_issuer.issue.assert_called_once_with(user.uuid)


class TestLoginUserFailure:
    async def test_raises_when_username_not_found(
        self, use_case: LoginUserUseCase, repository: UserRepositoryPort
    ) -> None:
        repository.find_by_username.return_value = None
        with pytest.raises(InvalidCredentialsError):
            await use_case.execute(username='ghost', password='plainpass1')

    async def test_raises_when_password_does_not_match(
        self, use_case: LoginUserUseCase, hasher: PasswordHasherPort
    ) -> None:
        hasher.verify.return_value = False
        with pytest.raises(InvalidCredentialsError):
            await use_case.execute(username='fabio01', password='wrongpass')

    async def test_raises_when_user_has_no_password(
        self, use_case: LoginUserUseCase, repository: UserRepositoryPort
    ) -> None:
        repository.find_by_username.return_value = _existing_user(
            username=None, password=None, facebook_token='fb_token_123'
        )
        with pytest.raises(InvalidCredentialsError):
            await use_case.execute(username='fabio01', password='plainpass1')

    async def test_does_not_issue_token_on_failure(
        self,
        use_case: LoginUserUseCase,
        repository: UserRepositoryPort,
        token_issuer: TokenIssuerPort,
    ) -> None:
        repository.find_by_username.return_value = None
        with pytest.raises(InvalidCredentialsError):
            await use_case.execute(username='ghost', password='plainpass1')
        token_issuer.issue.assert_not_called()
