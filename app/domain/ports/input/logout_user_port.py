from abc import ABC, abstractmethod


class LogoutUserPort(ABC):
    @abstractmethod
    def execute(self, token: str) -> None: ...
