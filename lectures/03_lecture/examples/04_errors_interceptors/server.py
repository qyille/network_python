"""
04_errors_interceptors / server.py — обработка ошибок + интерцепторы.

Запуск:
    python server.py
"""

from concurrent import futures
import logging

import grpc
import errors_pb2
import errors_pb2_grpc
from interceptor import LoggingInterceptor

logger = logging.getLogger(__name__)


class CalculatorServicer(errors_pb2_grpc.CalculatorServicer):

    def Divide(self, request, context):
        """Деление с обработкой zero division."""
        if request.b == 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Division by zero is not allowed")
            return errors_pb2.DivideResponse()
        return errors_pb2.DivideResponse(result=request.a / request.b)

    def Sqrt(self, request, context):
        """Квадратный корень. Отрицательное число → OUT_OF_RANGE."""
        if request.number < 0:
            context.set_code(grpc.StatusCode.OUT_OF_RANGE)
            context.set_details(
                f"Cannot compute sqrt of negative number: {request.number}"
            )
            return errors_pb2.SqrtResponse()
        return errors_pb2.SqrtResponse(result=request.number ** 0.5)


def serve(port: int = 50054):
    # Подключаем интерцептор
    interceptor = LoggingInterceptor()
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[interceptor],
    )
    errors_pb2_grpc.add_CalculatorServicer_to_server(CalculatorServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("Calculator gRPC-сервер c интерцептором запущен на порту %s", port)
    return server


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    serve().wait_for_termination()
