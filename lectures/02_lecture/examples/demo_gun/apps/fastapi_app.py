"""
FastAPI — асинхронный сервер.
Каждый эндпоинт помечен async def, используется await asyncio.sleep
для имитации I/O (например, поход в БД / внешний API).
"""

import asyncio
import time

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="FastAPI demo", description="Асинхронный сервер")


class ItemCreate(BaseModel):
    """Параметры создания товара — читаются из JSON-body."""
    name: str
    price: float


ITEMS = [
    {"id": 1, "name": "Товар A", "price": 100},
    {"id": 2, "name": "Товар B", "price": 200},
]


@app.get("/items")
async def get_items():
    """Список товаров — быстрый ответ без I/O."""
    return {"items": ITEMS, "count": len(ITEMS)}


@app.get("/items/sync")
def get_items_sync():
    """Синхронный эндпоинт внутри async FastAPI — всё равно работает."""
    time.sleep(0.05)
    return {"items": ITEMS, "count": len(ITEMS)}


@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """Один товар с симуляцией асинхронного I/O."""
    await asyncio.sleep(0.05)
    for item in ITEMS:
        if item["id"] == item_id:
            return {"item": item}
    return {"error": "Not found"}


@app.post("/items")
async def create_item(item: ItemCreate):
    """Создание товара с I/O симуляцией.

    FastAPI принимает Pydantic-модель ItemCreate из JSON-body
    и автоматически валидирует поля (name: str, price: float).
    """
    new_id = len(ITEMS) + 1
    await asyncio.sleep(0.03)
    new_item = {"id": new_id, "name": item.name, "price": item.price}
    ITEMS.append(new_item)
    return {"item": new_item}
