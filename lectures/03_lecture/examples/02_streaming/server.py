"""
02_streaming — 4 типа gRPC-стримов.

Запуск:
    python server.py
    # в другом терминале:
    python client.py
"""

from concurrent import futures
import logging
import time

import grpc
import streaming_pb2
import streaming_pb2_grpc

logger = logging.getLogger(__name__)

# In-memory хранилище
ITEMS = [
    streaming_pb2.Item(id=1, name="Молоко", price=89.9),
    streaming_pb2.Item(id=2, name="Хлеб", price=45.0),
    streaming_pb2.Item(id=3, name="Сыр", price=350.0),
    streaming_pb2.Item(id=4, name="Масло", price=199.0),
    streaming_pb2.Item(id=5, name="Яйца", price=129.0),
]


class DataServicer(streaming_pb2_grpc.DataServiceServicer):
    # ── 1. Unary ────────────────────────────────────────────────────────────
    def GetItem(
        self, request: streaming_pb2.ItemRequest, context
    ) -> streaming_pb2.Item:
        for item in ITEMS:
            if item.id == request.id:
                return item
        context.abort(grpc.StatusCode.NOT_FOUND, f"Item {request.id} not found")

    # ── 2. Server streaming ────────────────────────────────────────────────
    def ListItems(
        self, request: streaming_pb2.ListRequest, context
    ) -> list[streaming_pb2.Item]:
        """Возвращает items пачками — без буферизации всего списка в памяти."""
        count = 0
        for item in ITEMS:
            if request.filter and request.filter.lower() not in item.name.lower():
                continue
            if request.page_size and count >= request.page_size:
                break
            count += 1
            yield item

    # ── 3. Client streaming ────────────────────────────────────────────────
    def AddItems(self, request_iterator, context) -> streaming_pb2.Summary:
        """Принимает поток items от клиента."""
        total = 0
        total_price = 0.0
        for item in request_iterator:
            total += 1
            total_price += item.price
            logger.info("  Получен item: %s (%.2f)", item.name, item.price)
        return streaming_pb2.Summary(total=total, total_price=total_price)

    # ── 4. Bidirectional streaming ─────────────────────────────────────────
    def Chat(self, request_iterator, context):
        """Чат: каждый запрос → немедленный ответ."""
        seq = 0
        for msg in request_iterator:
            seq += 1
            yield streaming_pb2.ChatMessage(
                user="server",
                text=f"Эхо от {msg.user}: «{msg.text}»",
                seq=seq,
            )


def serve(port: int = 50052):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    streaming_pb2_grpc.add_DataServiceServicer_to_server(DataServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("Streaming-сервер запущен на порту %s", port)
    return server


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    serve().wait_for_termination()
