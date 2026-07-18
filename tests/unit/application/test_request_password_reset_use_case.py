from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.application.use_cases.request_password_reset import (
    RequestPasswordResetUseCase,
)
from app.domain.entities.password_reset_code import PasswordResetCode
from app.domain.entities.user import User
from app.domain.exceptions import (
    InvalidCellphoneError,
    PasswordResetAlreadyRequestedError,
    UserNotFoundError,
)
from app.domain.ports.output.password_reset_code_repository_port import (
    PasswordResetCodeRepositoryPort,
)
from app.domain.ports.output.sms_queue_port import SmsQueuePort
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


@pytest.fixture
def user_repository() -> UserRepositoryPort:
    repo = Mock(spec=UserRepositoryPort)
    repo.find_by_cellphone.return_value = _existing_user()
    return repo


@pytest.fixture
def reset_code_repository() -> PasswordResetCodeRepositoryPort:
    repo = Mock(spec=PasswordResetCodeRepositoryPort)
    repo.find_latest_by_user.return_value = None
    repo.exists_active_code.return_value = False
    repo.save.side_effect = lambda reset_code: reset_code
    return repo


@pytest.fixture
def sms_queue() -> SmsQueuePort:
    return Mock(spec=SmsQueuePort)


@pytest.fixture
def use_case(
    user_repository: UserRepositoryPort,
    reset_code_repository: PasswordResetCodeRepositoryPort,
    sms_queue: SmsQueuePort,
) -> RequestPasswordResetUseCase:
    return RequestPasswordResetUseCase(
        user_repository, reset_code_repository, sms_queue
    )


class TestRequestPasswordResetSuccess:
    async def test_generates_and_persists_a_six_digit_code(
        self,
        use_case: RequestPasswordResetUseCase,
        reset_code_repository: PasswordResetCodeRepositoryPort,
    ) -> None:
        await use_case.execute('+51 987654321')
        saved_code = reset_code_repository.save.call_args.args[0]
        assert isinstance(saved_code, PasswordResetCode)
        assert len(saved_code.code) == 6
        assert saved_code.code.isdigit()

    async def test_publishes_code_to_sms_queue(
        self, use_case: RequestPasswordResetUseCase, sms_queue: SmsQueuePort
    ) -> None:
        await use_case.execute('+51 987654321')
        sms_queue.publish_verification_code.assert_called_once()
        call = sms_queue.publish_verification_code.call_args
        assert call.kwargs['cellphone'] == '+51 987654321'
        assert len(call.kwargs['code']) == 6

    async def test_retries_generation_on_code_collision(
        self,
        use_case: RequestPasswordResetUseCase,
        reset_code_repository: PasswordResetCodeRepositoryPort,
    ) -> None:
        reset_code_repository.exists_active_code.side_effect = [True, False]
        await use_case.execute('+51 987654321')
        assert reset_code_repository.exists_active_code.call_count == 2


class TestRequestPasswordResetFailure:
    async def test_raises_on_invalid_cellphone_format(
        self, use_case: RequestPasswordResetUseCase
    ) -> None:
        with pytest.raises(InvalidCellphoneError):
            await use_case.execute('123')

    async def test_raises_when_user_not_found(
        self,
        use_case: RequestPasswordResetUseCase,
        user_repository: UserRepositoryPort,
    ) -> None:
        user_repository.find_by_cellphone.return_value = None
        with pytest.raises(UserNotFoundError):
            await use_case.execute('+51 987654321')

    async def test_does_not_publish_when_user_not_found(
        self,
        use_case: RequestPasswordResetUseCase,
        user_repository: UserRepositoryPort,
        sms_queue: SmsQueuePort,
    ) -> None:
        user_repository.find_by_cellphone.return_value = None
        with pytest.raises(UserNotFoundError):
            await use_case.execute('+51 987654321')
        sms_queue.publish_verification_code.assert_not_called()

    async def test_raises_when_code_already_requested_today(
        self,
        use_case: RequestPasswordResetUseCase,
        reset_code_repository: PasswordResetCodeRepositoryPort,
    ) -> None:
        reset_code_repository.find_latest_by_user.return_value = PasswordResetCode(
            user_uuid=uuid4(), code='111111', created_at=datetime.now(UTC)
        )
        with pytest.raises(PasswordResetAlreadyRequestedError):
            await use_case.execute('+51 987654321')

    async def test_allows_new_request_after_daily_limit_window(
        self,
        use_case: RequestPasswordResetUseCase,
        reset_code_repository: PasswordResetCodeRepositoryPort,
    ) -> None:
        reset_code_repository.find_latest_by_user.return_value = PasswordResetCode(
            user_uuid=uuid4(),
            code='111111',
            created_at=datetime.now(UTC) - timedelta(hours=25),
        )
        await use_case.execute('+51 987654321')
        reset_code_repository.save.assert_called_once()
