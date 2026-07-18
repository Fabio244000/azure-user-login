from abc import ABC, abstractmethod

from app.domain.entities.user import User


class LoginUserPort(ABC):
    @abstractmethod
    def execute(self, username: str, password: str) -> tuple[User, str]: ...
