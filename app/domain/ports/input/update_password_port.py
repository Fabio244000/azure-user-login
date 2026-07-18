from abc import ABC, abstractmethod


class UpdatePasswordPort(ABC):
    @abstractmethod
    def execute(self, cellphone: str, code: str, new_password: str) -> None: ...
