"""
04_errors_interceptors / interceptor.py — gRPC-интерцептор (middleware).

Интерцепторы в gRPC — аналог middleware в FastAPI/Flask.
Позволяют:
    - Логировать запросы
    - Замерять время выполнения
    - Обрабатывать ошибки централизованно
    - Добавлять аутентификацию
"""

import logging
import time
from typing import Callable, Any

import grpc

logger = logging.getLogger(__name__)


class LoggingInterceptor(grpc.ServerInterceptor):
    """
    Унитарный интерцептор (unary-unary).

    Перехватывает все unary-вызовы, логирует их и замеряет время.
    """

    def intercept_service(self, continuation: Callable, handler_call_details: grpc.HandlerCallDetails) -> Any:
        """Вызывается для каждого gRPC-метода при регистрации сервера."""

        # Имя метода (например, /errors.Calculator/Divide)
        method_name = handler_call_details.method

        # Оборачиваем обработчик
        return self._wrap_handler(continuation(handler_call_details), method_name)

    def _wrap_handler(self, handler, method_name: str):
        """Оборачивает unary-обработчик."""

        if not handler:
            return handler

        # Для unary-методов
        if hasattr(handler, "unary_unary"):

            class _Wrapper:
                @staticmethod
                def __call__(request, context):
                    t0 = time.perf_counter()
                    try:
                        response = handler.unary_unary(request, context)
                        elapsed = time.perf_counter() - t0
                        logger.info("[%s] → OK (%.2fms)", method_name, elapsed * 1000)
                        return response
                    except grpc.RpcError:
                        elapsed = time.perf_counter() - t0
                        logger.warning("[%s] → ERROR (%.2fms)", method_name, elapsed * 1000)
                        raise

            return _Wrapper()

        return handler
