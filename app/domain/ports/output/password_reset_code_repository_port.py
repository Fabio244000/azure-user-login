from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.password_reset_code import PasswordResetCode


class PasswordResetCodeRepositoryPort(ABC):
    @abstractmethod
    async def save(self, reset_code: PasswordResetCode) -> PasswordResetCode: ...

    @abstractmethod
    async def update(self, reset_code: PasswordResetCode) -> PasswordResetCode: ...

    @abstractmethod
    async def find_latest_by_user(
        self, user_uuid: UUID
    ) -> PasswordResetCode | None: ...

    @abstractmethod
    async def exists_active_code(self, code: str) -> bool: ...
