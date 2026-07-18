from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.domain.entities.password_reset_code import PasswordResetCode
from app.domain.exceptions import InvalidPasswordResetCodeError


class TestPasswordResetCodeCreation:
    def test_valid_code_builds_entity(self) -> None:
        reset_code = PasswordResetCode(user_uuid=uuid4(), code='123456')
        assert reset_code.code == '123456'
        assert reset_code.attempts_used == 0
        assert reset_code.consumed_at is None

    def test_expires_at_defaults_to_ten_minutes_after_created_at(self) -> None:
        reset_code = PasswordResetCode(user_uuid=uuid4(), code='123456')
        assert reset_code.expires_at == reset_code.created_at + timedelta(minutes=10)

    def test_explicit_expires_at_is_respected(self) -> None:
        created_at = datetime.now(UTC)
        expires_at = created_at + timedelta(minutes=1)
        reset_code = PasswordResetCode(
            user_uuid=uuid4(),
            code='123456',
            created_at=created_at,
            expires_at=expires_at,
        )
        assert reset_code.expires_at == expires_at


class TestPasswordResetCodeValidation:
    def test_code_with_letters_is_invalid(self) -> None:
        with pytest.raises(InvalidPasswordResetCodeError):
            PasswordResetCode(user_uuid=uuid4(), code='12345a')

    def test_code_shorter_than_six_digits_is_invalid(self) -> None:
        with pytest.raises(InvalidPasswordResetCodeError):
            PasswordResetCode(user_uuid=uuid4(), code='12345')

    def test_code_longer_than_six_digits_is_invalid(self) -> None:
        with pytest.raises(InvalidPasswordResetCodeError):
            PasswordResetCode(user_uuid=uuid4(), code='1234567')
