import json
import uuid
from collections.abc import AsyncGenerator

import pytest
from azure.storage.queue.aio import QueueClient

from app.infrastructure.messaging.azure_sms_queue import AzureSmsQueue
from config.settings import settings


@pytest.fixture
def queue_name() -> str:
    return f'test-sms-queue-{uuid.uuid4().hex[:12]}'


@pytest.fixture
async def queue_client(queue_name: str) -> AsyncGenerator[QueueClient, None]:
    client = QueueClient.from_connection_string(
        conn_str=settings.queue_connection_string, queue_name=queue_name
    )
    async with client:
        yield client
        await client.delete_queue()


class TestAzureSmsQueue:
    async def test_publish_creates_queue_and_sends_message(
        self, queue_name: str, queue_client: QueueClient
    ) -> None:
        sms_queue = AzureSmsQueue(queue_name=queue_name)
        await sms_queue.publish_verification_code(
            cellphone='+51 987654321', code='123456'
        )

        received = [
            message
            async for message in queue_client.receive_messages(messages_per_page=1)
        ]
        assert len(received) == 1
        payload = json.loads(received[0].content)
        assert payload == {'cellphone': '+51 987654321', 'code': '123456'}
