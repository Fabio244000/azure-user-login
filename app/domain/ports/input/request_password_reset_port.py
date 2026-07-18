from abc import ABC, abstractmethod


class RequestPasswordResetPort(ABC):
    @abstractmethod
    def execute(self, cellphone: str) -> None: ...
