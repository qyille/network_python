"""
02_streaming — демонстрация 4 типов gRPC-вызовов на клиенте.
"""

import logging

import grpc
import streaming_pb2
import streaming_pb2_grpc

logger = logging.getLogger(__name__)


def run(target: str = "localhost:50052"):
    channel = grpc.insecure_channel(target)
    stub = streaming_pb2_grpc.DataServiceStub(channel)

    # ── 1. Unary ────────────────────────────────────────────────────────────
    logger.info("═══ 1. Unary: GetItem(2) ═══")
    item = stub.GetItem(streaming_pb2.ItemRequest(id=2))
    logger.info("  Ответ: id=%s name=%s price=%.2f", item.id, item.name, item.price)

    # ── 2. Server streaming ────────────────────────────────────────────────
    logger.info("═══ 2. Server streaming: ListItems(page_size=3) ═══")
    for item in stub.ListItems(streaming_pb2.ListRequest(page_size=3, filter="")):
        logger.info("  → %s: %s (%.2f)", item.id, item.name, item.price)

    # ── 3. Client streaming ────────────────────────────────────────────────
    logger.info("═══ 3. Client streaming: AddItems ═══")

    def make_items():
        for name, price in [("Помидор", 250), ("Огурец", 180), ("Перец", 320)]:
            yield streaming_pb2.Item(name=name, price=price)

    summary = stub.AddItems(make_items())
    logger.info("  Итого: %d товаров на %.2f", summary.total, summary.total_price)

    # ── 4. Bidirectional streaming ─────────────────────────────────────────
    logger.info("═══ 4. Bidirectional: Chat ═══")

    def chat_messages():
        for user, text in [("Алиса", "Привет!"), ("Боб", "Как дела?"), ("Алиса", "Норм")]:
            yield streaming_pb2.ChatMessage(user=user, text=text)

    for reply in stub.Chat(chat_messages()):
        logger.info("  [%s] seq=%s: %s", reply.user, reply.seq, reply.text)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run()
