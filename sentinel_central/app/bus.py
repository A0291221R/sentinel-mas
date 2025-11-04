import aio_pika, asyncio, json, os
from typing import Callable, Awaitable, Any, Dict

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")

import logging
log = logging.getLogger(__name__)

class MessageBus:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.connection = None
        self.channel = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(RABBITMQ_URL, loop=self.loop)
        self.channel = await self.connection.channel()

    async def publish(self, queue_name: str, message: Dict[str, Any]):
        await self.channel.declare_queue(queue_name, durable=True)
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                content_type="application/json"
            ),
            routing_key=queue_name,
        )
        log.info(f"Published to {queue_name}")
        log.debug(f"message: {message}")

    async def publish_envelope(self, envelope: Dict[str, Any]):
        queue_name = envelope.get("type", "unknown")
        await self.publish(queue_name, envelope)

    async def subscribe(self, queue_name: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]):
        queue = await self.channel.declare_queue(queue_name, durable=True)

        async def callback(message: aio_pika.IncomingMessage):
            async with message.process():
                payload = json.loads(message.body.decode())
                await handler(payload)

        await queue.consume(callback)
        log.info(f"Subscribed to {queue_name}")
