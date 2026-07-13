"""
01_hello_grpc — gRPC-клиент "Greeter".

Запуск (после server.py):
    python client.py

Убедитесь, что server.py запущен на порту 50051.
"""

import logging

import grpc
import hello_pb2
import hello_pb2_grpc

logger = logging.getLogger(__name__)


def run(target: str = "localhost:50051"):
    """Подключается к gRPC-серверу и отправляет запрос SayHello."""
    # 1. Создаём канал (channel) — соединение с сервером
    with grpc.insecure_channel(target) as channel:
        # 2. Создаём stub — клиентскую заглушку с теми же методами, что у сервера
        stub = hello_pb2_grpc.GreeterStub(channel)

        # 3. Вызываем remote-метод как обычную функцию
        response = stub.SayHello(hello_pb2.HelloRequest(name="Даниэль"))

    logger.info("Ответ от сервера: %s", response.message)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    run()
