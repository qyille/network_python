"""
04_errors_interceptors / client.py — обработка ошибок на клиенте.

Показывает, как ловить и разбирать gRPC-ошибки.
"""

import logging

import grpc
import errors_pb2
import errors_pb2_grpc

logger = logging.getLogger(__name__)


def run(target: str = "localhost:50054"):
    channel = grpc.insecure_channel(target)
    stub = errors_pb2_grpc.CalculatorStub(channel)

    # ── Успешный вызов ──────────────────────────────────────────────────────
    logger.info("═══ Divide(10, 2) ═══")
    resp = stub.Divide(errors_pb2.DivideRequest(a=10, b=2))
    logger.info("  10 / 2 = %s", resp.result)

    # ── ZeroDivisionError → INVALID_ARGUMENT ────────────────────────────────
    logger.info("═══ Divide(10, 0) — ожидаем ошибку ═══")
    try:
        stub.Divide(errors_pb2.DivideRequest(a=10, b=0))
    except grpc.RpcError as e:
        logger.info("  Код ошибки: %s", e.code())           # INVALID_ARGUMENT
        logger.info("  Сообщение: %s", e.details())          # Division by zero
        logger.info("  (в REST это был бы HTTP 400)")

    # ── Sqrt от отрицательного → OUT_OF_RANGE ──────────────────────────────
    logger.info("═══ Sqrt(-4) — ожидаем ошибку ═══")
    try:
        stub.Sqrt(errors_pb2.SqrtRequest(number=-4))
    except grpc.RpcError as e:
        logger.info("  Код ошибки: %s", e.code())           # OUT_OF_RANGE
        logger.info("  Сообщение: %s", e.details())

    # ── Сравнение с REST ────────────────────────────────────────────────────
    logger.info("")
    logger.info("📌 Сравнение обработки ошибок:")
    logger.info("  REST:   HTTP 400 + JSON {\"detail\": \"...\"}")
    logger.info("  gRPC:   grpc.StatusCode.INVALID_ARGUMENT + details()")
    logger.info("  gRPC   → машинно-читаемые коды (машина знает, что делать)")
    logger.info("  REST   → человеко-читаемый JSON (человек читает сообщение)")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run()
