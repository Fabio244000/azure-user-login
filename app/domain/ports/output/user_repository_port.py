from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.user import User


class UserRepositoryPort(ABC):
    @abstractmethod
    async def save(self, user: User) -> User: ...

    @abstractmethod
    async def find_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    async def find_by_cellphone(self, cellphone: str) -> User | None: ...

    @abstractmethod
    async def update_password(self, user_uuid: UUID, hashed_password: str) -> None: ...

    @abstractmethod
    async def exists_by_username(self, username: str) -> bool: ...

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool: ...

    @abstractmethod
    async def exists_by_cellphone(self, cellphone: str) -> bool: ...
