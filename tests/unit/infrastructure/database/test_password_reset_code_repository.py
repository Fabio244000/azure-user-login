from datetime import UTC, datetime, timedelta

import pytest

from app.domain.entities.password_reset_code import PasswordResetCode
from app.domain.entities.user import User
from app.infrastructure.database.repositories.password_reset_code_repository import (
    PasswordResetCodeRepository,
)
from app.infrastructure.database.repositories.user_repository import UserRepository


def _valid_user(**overrides):
    data = {
        'first_name': 'fabio',
        'last_name': 'nunez garcia',
        'cellphone': '+51 987654321',
        'username': 'fabio01',
        'password': 'hashedpassword123',
        'email': 'fabio@mail.com',
    }
    data.update(overrides)
    return User(**data)


@pytest.fixture
async def user(session):
    return await UserRepository(session).save(_valid_user())


class TestPasswordResetCodeRepositorySave:
    async def test_saves_and_returns_the_code(self, session, user):
        repository = PasswordResetCodeRepository(session)
        reset_code = PasswordResetCode(user_uuid=user.uuid, code='123456')
        saved = await repository.save(reset_code)
        assert saved.uuid == reset_code.uuid


class TestPasswordResetCodeRepositoryUpdate:
    async def test_persists_incremented_attempts(self, session, user):
        repository = PasswordResetCodeRepository(session)
        reset_code = await repository.save(
            PasswordResetCode(user_uuid=user.uuid, code='777777')
        )
        reset_code.attempts_used += 1
        await repository.update(reset_code)

        latest = await repository.find_latest_by_user(user.uuid)
        assert latest is not None
        assert latest.attempts_used == 1

    async def test_persists_consumed_at(self, session, user):
        repository = PasswordResetCodeRepository(session)
        reset_code = await repository.save(
            PasswordResetCode(user_uuid=user.uuid, code='888888')
        )
        reset_code.consumed_at = datetime.now(UTC)
        await repository.update(reset_code)

        assert await repository.exists_active_code('888888') is False


class TestPasswordResetCodeRepositoryFindLatestByUser:
    async def test_returns_none_when_no_code_exists(self, session, user):
        repository = PasswordResetCodeRepository(session)
        assert await repository.find_latest_by_user(user.uuid) is None

    async def test_returns_the_most_recent_code(self, session, user):
        repository = PasswordResetCodeRepository(session)
        older = PasswordResetCode(
            user_uuid=user.uuid,
            code='111111',
            created_at=datetime.now(UTC) - timedelta(hours=2),
        )
        newer = PasswordResetCode(
            user_uuid=user.uuid, code='222222', created_at=datetime.now(UTC)
        )
        await repository.save(older)
        await repository.save(newer)

        latest = await repository.find_latest_by_user(user.uuid)
        assert latest is not None
        assert latest.code == '222222'


class TestPasswordResetCodeRepositoryExistsActiveCode:
    async def test_true_for_a_non_expired_unconsumed_code(self, session, user):
        repository = PasswordResetCodeRepository(session)
        await repository.save(PasswordResetCode(user_uuid=user.uuid, code='333333'))
        assert await repository.exists_active_code('333333') is True

    async def test_false_for_an_unknown_code(self, session, user):
        repository = PasswordResetCodeRepository(session)
        assert await repository.exists_active_code('999999') is False

    async def test_false_for_an_expired_code(self, session, user):
        repository = PasswordResetCodeRepository(session)
        expired = PasswordResetCode(
            user_uuid=user.uuid,
            code='444444',
            created_at=datetime.now(UTC) - timedelta(minutes=20),
            expires_at=datetime.now(UTC) - timedelta(minutes=10),
        )
        await repository.save(expired)
        assert await repository.exists_active_code('444444') is False

    async def test_false_for_a_consumed_code(self, session, user):
        repository = PasswordResetCodeRepository(session)
        consumed = PasswordResetCode(
            user_uuid=user.uuid, code='555555', consumed_at=datetime.now(UTC)
        )
        await repository.save(consumed)
        assert await repository.exists_active_code('555555') is False
