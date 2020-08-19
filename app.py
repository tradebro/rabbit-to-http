from os import environ
import asyncio
import uvloop
import aio_pika
import ujson
import httpx

AMQP_CONN_STRING = environ.get('AMQP_CONN_STRING')
AMQP_QUEUE = environ.get('AMQP_QUEUE')
AMQP_ORDERS_EXCHANGE = environ.get('AMQP_ORDERS_EXCHANGE')
HTTP_ENDPOINT = environ.get('HTTP_ENDPOINT')

uvloop.install()


async def forward_to_http_endpoint(message_body: dict) -> bool:
    try:
        response: httpx.Response = httpx.post(url=HTTP_ENDPOINT,
                                              json=message_body)
    except httpx.HTTPError:
        return False
    except httpx.InvalidURL:
        return False
    except httpx.StreamError:
        return False

    valid_status_codes = [
        200,
        201,
        204
    ]

    return response.status_code in valid_status_codes


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process(ignore_processed=True):
        message_body = ujson.loads(message.body)
        forwarded = await forward_to_http_endpoint(message_body=message_body)
        if not forwarded:
            await message.nack(requeue=False)
            return

        await message.ack()


async def main(aio_loop) -> aio_pika.Connection:
    conn: aio_pika.Connection = await aio_pika.connect_robust(url=AMQP_CONN_STRING,
                                                              loop=aio_loop)

    channel = await conn.channel()
    exchange = await channel.declare_exchange(name=AMQP_ORDERS_EXCHANGE,
                                              type=aio_pika.ExchangeType.FANOUT)
    queue = await channel.declare_queue(name=AMQP_QUEUE,
                                        auto_delete=True)

    await queue.bind(exchange)
    await queue.consume(process_message)

    return conn


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    connection = loop.run_until_complete(main(aio_loop=loop))

    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(connection.close())
