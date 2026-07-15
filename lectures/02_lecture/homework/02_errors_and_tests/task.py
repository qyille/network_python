"""
02_errors_and_tests — чиним и тестируем 🛠️

В app.py лежит сломанное FastAPI-приложение. Найдите и исправьте ВСЕ проблемы.

Задача А: Исправить приложение (task.py)
    Скопируйте app.py сюда и исправьте все ошибки.
    Внимание: tests будут проверять ВАШУ реализацию, не оригинальный app.py.

    Чего ждут тесты:
        ✓ POST /items → 201 Created
        ✓ GET  /items/{id} → 200 или 404
        ✓ PUT  /items/{id} → 200 или 404
        ✓ DELETE /items/{id} → 204 или 404
        ✓ GET  /divide?a=10&b=0 → 400 (не 500!)
        ✓ GET  /items/{id}/counter → race condition отсутствует
        ✓ GET  /slow-sync → async def + await asyncio.sleep
        ✓ DELETE возвращает правильный статус (204)
"""

import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

app = FastAPI()

ITEMS: dict[int, dict] = {}
NEXT_ID = 1
COUNTER = 0


class ItemCreate(BaseModel):
    name: str = Field(min_length=1)


class ItemUpdate(BaseModel):
    name: str = Field(min_length=1)


class ItemNotFoundException(Exception):
    """Предмет не найден."""
    pass


@app.exception_handler(ItemNotFoundException)
async def item_not_found_handler(request: Request, exc: ItemNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": "Item not found"}
    )


@app.exception_handler(ZeroDivisionError)
async def zero_division_handler(request: Request, exc: ZeroDivisionError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Division by zero is not allowed"}
    )


# ═══════════════════════════════════════════════════════════
# ЭНДПОИНТЫ
# ═══════════════════════════════════════════════════════════


@app.get("/items")
def list_items():
    return {"items": list(ITEMS.values())}


@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id not in ITEMS:
        raise ItemNotFoundException()
    return ITEMS[item_id]


@app.post("/items", status_code=201)
def create_item(item: ItemCreate):
    global NEXT_ID

    new_item = {
        "id": NEXT_ID,
        "name": item.name
    }
    ITEMS[NEXT_ID] = new_item
    NEXT_ID += 1

    return new_item


@app.put("/items/{item_id}")
def update_item(item_id: int, update: ItemUpdate):
    if item_id not in ITEMS:
        raise ItemNotFoundException()

    ITEMS[item_id]["name"] = update.name
    return ITEMS[item_id]


@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    if item_id not in ITEMS:
        raise ItemNotFoundException()

    del ITEMS[item_id]
    return Response(status_code=204)


@app.get("/items/{item_id}/counter")
def get_counter(item_id: int):
    if item_id not in ITEMS:
        raise ItemNotFoundException()

    global COUNTER
    COUNTER += 1
    return {"counter": COUNTER}


@app.get("/divide")
def divide(a: int, b: int):
    if b == 0:
        raise ZeroDivisionError("Division by zero")
    return {"result": a / b}


@app.get("/slow-sync")
async def slow_sync():
    await asyncio.sleep(0.5)
    return {"status": "done"}