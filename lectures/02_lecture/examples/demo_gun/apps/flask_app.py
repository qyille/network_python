"""Flask — синхронный сервер для нагрузочного тестирования."""

import time

from flask import Flask, jsonify, request

app = Flask(__name__)

ITEMS = [
    {"id": 1, "name": "Товар A", "price": 100},
    {"id": 2, "name": "Товар B", "price": 200},
]


@app.route("/items")
def get_items():
    """Список товаров — быстрый ответ."""
    return jsonify({"items": ITEMS, "count": len(ITEMS)})


@app.route("/items/sync")
def get_items_sync():
    """Эндпоинт с синхронным sleep — блокирует воркер."""
    time.sleep(0.05)
    return jsonify({"items": ITEMS, "count": len(ITEMS)})


@app.route("/items/<int:item_id>")
def get_item(item_id):
    """Один товар с симуляцией I/O (time.sleep)."""
    time.sleep(0.05)
    for item in ITEMS:
        if item["id"] == item_id:
            return jsonify({"item": item})
    return jsonify({"error": "Not found"}), 404


@app.route("/items", methods=["POST"])
def create_item():
    """Создание товара."""
    data = request.get_json(force=True)
    time.sleep(0.03)
    new_id = len(ITEMS) + 1
    item = {"id": new_id, "name": data["name"], "price": data["price"]}
    ITEMS.append(item)
    return jsonify({"item": item}), 201


if __name__ == "__main__":
    app.run(port=8002)
