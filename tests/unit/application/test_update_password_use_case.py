from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.application.use_cases.update_password import UpdatePasswordUseCase
from app.domain.entities.password_reset_code import PasswordResetCode
from app.domain.entities.user import User
from app.domain.exceptions import (
    InvalidPasswordError,
    InvalidPasswordResetCodeError,
    PasswordResetAttemptsExceededError,
    UserNotFoundError,
)
from app.domain.ports.output.password_hasher_port import PasswordHasherPort
from app.domain.ports.output.password_reset_code_repository_port import (
    PasswordResetCodeRepositoryPort,
)
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
    return User(**data)


def _active_reset_code(**overrides: Any) -> PasswordResetCode:
    data: dict[str, Any] = {'user_uuid': uuid4(), 'code': '123456'}
    data.update(overrides)
    return PasswordResetCode(**data)


@pytest.fixture
def user_repository() -> UserRepositoryPort:
    repo = Mock(spec=UserRepositoryPort)
    repo.find_by_cellphone.return_value = _existing_user()
    return repo


@pytest.fixture
def reset_code_repository() -> PasswordResetCodeRepositoryPort:
    repo = Mock(spec=PasswordResetCodeRepositoryPort)
    repo.find_latest_by_user.return_value = _active_reset_code()
    repo.update.side_effect = lambda reset_code: reset_code
    return repo


@pytest.fixture
def hasher() -> PasswordHasherPort:
    hasher = Mock(spec=PasswordHasherPort)
    hasher.hash.return_value = 'hashed-new-password'
    return hasher


@pytest.fixture
def use_case(
    user_repository: UserRepositoryPort,
    reset_code_repository: PasswordResetCodeRepositoryPort,
    hasher: PasswordHasherPort,
) -> UpdatePasswordUseCase:
    return UpdatePasswordUseCase(user_repository, reset_code_repository, hasher)


class TestUpdatePasswordSuccess:
    async def test_updates_the_user_password(
        self,
        use_case: UpdatePasswordUseCase,
        user_repository: UserRepositoryPort,
    ) -> None:
        user = user_repository.find_by_cellphone.return_value
        await use_case.execute('+51 987654321', '123456', 'newsecret123')
        user_repository.update_password.assert_called_once_with(
            user.uuid, 'hashed-new-password'
        )

    async def test_marks_the_code_as_consumed(
        self,
        use_case: UpdatePasswordUseCase,
        reset_code_repository: PasswordResetCodeRepositoryPort,
    ) -> None:
        await use_case.execute('+51 987654321', '123456', 'newsecret123')
        updated_code = reset_code_repository.update.call_args.args[0]
        assert updated_code.consumed_at is not None


class TestUpdatePasswordFailure:
    async def test_raises_when_user_not_found(
        self, use_case: UpdatePasswordUseCase, user_repository: UserRepositoryPort
    ) -> None:
        user_repository.find_by_cellphone.return_value = None
        with pytest.raises(UserNotFoundError):
            await use_case.execute('+51 987654321', '123456', 'newsecret123')

    async def test_raises_when_no_active_code_exists(
        self,
        use_case: UpdatePasswordUseCase,
        reset_code_repository: PasswordResetCodeRepositoryPort,
    ) -> None:
        reset_code_repository.find_latest_by_user.return_value = None
        with pytest.raises(InvalidPasswordResetCodeError):
            await use_case.execute('+51 987654321', '123456', 'newsecret123')

    async def test_raises_when_code_already_consumed(
        self,
        use_case: UpdatePasswordUseCase,
        reset_code_repository: PasswordResetCodeRepositoryPort,
    ) -> None:
        reset_code_repository.find_latest_by_user.return_value = _active_reset_code(
            consumed_at=datetime.now(UTC)
        )
        with pytest.raises(InvalidPasswordResetCodeError):
            await use_case.execute('+51 987654321', '123456', 'newsecret123')

    async def test_raises_when_code_expired(
        self,
        use_case: UpdatePasswordUseCase,
        reset_code_repository: PasswordResetCodeRepositoryPort,
    ) -> None:
        reset_code_repository.find_latest_by_user.return_value = _active_reset_code(
            created_at=datetime.now(UTC) - timedelta(minutes=20),
            expires_at=datetime.now(UTC) - timedelta(minutes=10),
        )
        with pytest.raises(InvalidPasswordResetCodeError):
            await use_case.execute('+51 987654321', '123456', 'newsecret123')

    async def test_raises_when_attempts_exceeded(
        self,
        use_case: UpdatePasswordUseCase,
        reset_code_repository: PasswordResetCodeRepositoryPort,
    ) -> None:
        reset_code_repository.find_latest_by_user.return_value = _active_reset_code(
            attempts_used=3
        )
        with pytest.raises(PasswordResetAttemptsExceededError):
            await use_case.execute('+51 987654321', '123456', 'newsecret123')

    async def test_wrong_code_increments_attempts_and_raises(
        self,
        use_case: UpdatePasswordUseCase,
        reset_code_repository: PasswordResetCodeRepositoryPort,
    ) -> None:
        with pytest.raises(InvalidPasswordResetCodeError):
            await use_case.execute('+51 987654321', '999999', 'newsecret123')

        updated_code = reset_code_repository.update.call_args.args[0]
        assert updated_code.attempts_used == 1
        assert updated_code.consumed_at is None

    async def test_wrong_code_does_not_touch_user_password(
        self,
        use_case: UpdatePasswordUseCase,
        user_repository: UserRepositoryPort,
    ) -> None:
        with pytest.raises(InvalidPasswordResetCodeError):
            await use_case.execute('+51 987654321', '999999', 'newsecret123')
        user_repository.update_password.assert_not_called()

    async def test_raises_on_invalid_new_password_format(
        self,
        use_case: UpdatePasswordUseCase,
        reset_code_repository: PasswordResetCodeRepositoryPort,
    ) -> None:
        with pytest.raises(InvalidPasswordError):
            await use_case.execute('+51 987654321', '123456', 'short')

    async def test_invalid_password_format_does_not_consume_an_attempt(
        self,
        use_case: UpdatePasswordUseCase,
        reset_code_repository: PasswordResetCodeRepositoryPort,
    ) -> None:
        with pytest.raises(InvalidPasswordError):
            await use_case.execute('+51 987654321', '123456', 'short')
        reset_code_repository.update.assert_not_called()
