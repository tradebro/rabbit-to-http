from os import environ
import asyncio
import uvloop
import aio_pika
import ujson
import httpx

AMQP_CONN_STRING = environ.get('AMQP_CONN_STRING')
AMQP_QUEUE = environ.get('AMQP_QUEUE')
HTTP_ENDPOINT = environ.get('HTTP_ENDPOINT')

uvloop.install()


async def forward_to_http_endpoint(message_body: dict) -> bool:
    response: httpx.Response = httpx.post(url=HTTP_ENDPOINT,
                                          data=message_body)
    valid_status_codes = [
        200,
        201,
        204
    ]

    return response.status_code in valid_status_codes


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        message_body = ujson.loads(message.body)
        forwarded = forward_to_http_endpoint(message_body=message_body)
        if not forwarded:
            await message.nack(requeue=True)
            return

        await message.ack()


async def main(aio_loop) -> aio_pika.Connection:
    connection: aio_pika.Connection = await aio_pika.connect_robust(url=AMQP_CONN_STRING,
                                                                    loop=aio_loop)

    channel: aio_pika.Channel = await connection.channel()
    queue: aio_pika.Queue = await channel.declare_queue(name=AMQP_QUEUE,
                                                        auto_delete=True)

    await queue.consume(process_message)

    return connection


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(aio_loop=loop))
    loop.close()
