# Rabbit to HTTP

This is a generic RabbitMQ consumer always forwarding messages to an HTTP endpoint.

## Env Vars

| Name | Description |
| :--- | :--- |
| `AMQP_CONN_STRING` | Required string |
| `AMQP_QUEUE` | Required string, also known as routing key |
| `AMQP_ORDERS_EXCHANGE` | Required string |
| `HTTP_ENDPOINT` | HTTP Endpoint to forward to |

## How It Works

It forwards all messages consumed with a few assumptions expected to be true:

* Message body is a valid JSON
* The HTTP endpoint receives `POST` requests accepting `application/json` body
* No processing is done to the message body, forwards as is
* Acknowledge (ack) messages when the HTTP endpoints returns with a `[200, 201, 204]` status code
* Does not acknowledge (nack) when the HTTP endpoints does not return with the above status codes and requeues

## Running

```shell
$ python3 -m virtualenv
$ virtualenv env
$ . env/bin/activate
$ pip install -r requirements.txt
$ ./run-local.sh
```

### Docker

Any commits pushed to the `master` branch will automatically push docker images to `tistaharahap/rabbit-to-http:latest`.

```shell
$ docker run -d --name tv-alerts -e AMQP_CONN_STRING=your_conn_string -e AMQP_QUEUE=your_queue -e HTTP_ENDPOINT=your_endpoint tistaharahap/rabit-to-http:latest
```
