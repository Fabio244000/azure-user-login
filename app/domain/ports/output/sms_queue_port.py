from abc import ABC, abstractmethod


class SmsQueuePort(ABC):
    @abstractmethod
    async def publish_verification_code(self, cellphone: str, code: str) -> None: ...
