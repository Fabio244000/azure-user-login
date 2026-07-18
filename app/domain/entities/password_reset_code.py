from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.domain.constants import (
    PASSWORD_RESET_CODE_PATTERN,
    PASSWORD_RESET_CODE_TTL_MINUTES,
)
from app.domain.exceptions import InvalidPasswordResetCodeError


@dataclass
class PasswordResetCode:
    user_uuid: UUID
    code: str
    attempts_used: int = 0
    consumed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    uuid: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not PASSWORD_RESET_CODE_PATTERN.match(self.code):
            raise InvalidPasswordResetCodeError('code must be exactly 6 digits.')
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(
                minutes=PASSWORD_RESET_CODE_TTL_MINUTES
            )
