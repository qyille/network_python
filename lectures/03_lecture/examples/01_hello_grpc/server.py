"""
01_hello_grpc — gRPC-сервер "Greeter".

Запуск:
    python server.py

После запуска сервер слушает порт 50051.
Проверить можно client.py.
"""

from concurrent import futures
import logging

import grpc
import hello_pb2
import hello_pb2_grpc

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Реализация сервиса
# ═══════════════════════════════════════════════════════════════════════════════


class GreeterServicer(hello_pb2_grpc.GreeterServicer):
    """Реализует методы, описанные в hello.proto."""

    def SayHello(
        self, request: hello_pb2.HelloRequest, context: grpc.ServicerContext
    ) -> hello_pb2.HelloReply:
        """Обрабатывает SayHello — простейший unary-вызов."""
        logger.info("Получен запрос: name=%s", request.name)
        return hello_pb2.HelloReply(message=f"Hello, {request.name}!")


# ═══════════════════════════════════════════════════════════════════════════════
# Запуск сервера
# ═══════════════════════════════════════════════════════════════════════════════


def serve(port: int = 50051) -> grpc.Server:
    """Создаёт и запускает gRPC-сервер."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    hello_pb2_grpc.add_GreeterServicer_to_server(GreeterServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("gRPC-сервер запущен на порту %s", port)
    return server


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    server = serve()
    server.wait_for_termination()
