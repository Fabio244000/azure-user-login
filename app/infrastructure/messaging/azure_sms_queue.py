import json

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.queue.aio import QueueClient

from app.domain.ports.output.sms_queue_port import SmsQueuePort
from config.settings import settings


class AzureSmsQueue(SmsQueuePort):
    def __init__(self, queue_name: str | None = None) -> None:
        self._queue_name = queue_name or settings.sms_queue_name

    async def publish_verification_code(self, cellphone: str, code: str) -> None:
        message = json.dumps({'cellphone': cellphone, 'code': code})
        async with self._client() as queue_client:
            try:
                await queue_client.send_message(message)
            except ResourceNotFoundError:
                await queue_client.create_queue()
                await queue_client.send_message(message)

    def _client(self) -> QueueClient:
        return QueueClient.from_connection_string(
            conn_str=settings.queue_connection_string,
            queue_name=self._queue_name,
        )
