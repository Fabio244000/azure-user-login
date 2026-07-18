import asyncio
import contextlib
import json
import logging

from azure.core.exceptions import ResourceExistsError
from azure.storage.queue.aio import QueueClient

from config.settings import settings

logging.basicConfig(
    level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger('sms_worker')
logger.setLevel(logging.INFO)

POLL_INTERVAL_SECONDS = 2


async def run() -> None:
    async with QueueClient.from_connection_string(
        conn_str=settings.queue_connection_string,
        queue_name=settings.sms_queue_name,
    ) as queue_client:
        await _ensure_queue_exists(queue_client)
        logger.info('sms worker listening on queue %r', settings.sms_queue_name)
        while True:
            await _consume_pending_messages(queue_client)
            await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def _ensure_queue_exists(queue_client: QueueClient) -> None:
    with contextlib.suppress(ResourceExistsError):
        await queue_client.create_queue()


async def _consume_pending_messages(queue_client: QueueClient) -> None:
    messages = queue_client.receive_messages(messages_per_page=10)
    async for message in messages:
        _send_sms(message.content)
        await queue_client.delete_message(message)


def _send_sms(raw_message: str) -> None:
    payload = json.loads(raw_message)
    logger.info(
        '[SMS MOCK] to %s: your verification code is %s',
        payload['cellphone'],
        payload['code'],
    )


if __name__ == '__main__':
    asyncio.run(run())
