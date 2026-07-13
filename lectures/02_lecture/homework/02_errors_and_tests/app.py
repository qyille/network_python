"""
02_errors_and_tests — сломанное приложение 🐛

Здесь есть несколько проблем. Ваша задача — найти их все и исправить.

Ваша реализация — в task.py. tests будут проверять ИСПРАВЛЕННУЮ версию.
"""

import time
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

ITEMS = [
    {"id": 1, "name": "Item 1"},
    {"id": 2, "name": "Item 2"},
]

COUNTER = 0


class ItemCreate(BaseModel):
    name: str


class ItemUpdate(BaseModel):
    name: str = ""
    unknown_field: str


@app.get("/items")
def list_items():
    return {"items": ITEMS}


@app.get("/items/{item_id}")
def get_item(item_id: int):
    return ITEMS[item_id]


@app.post("/items")
def create_item(item: ItemCreate):
    new_id = len(ITEMS) + 1
    ITEMS.append({"id": new_id, "name": item.name})
    return {"id": new_id}


@app.get("/items/{item_id}/counter")
def get_counter(item_id: int):
    global COUNTER
    COUNTER += 1
    return {"counter": COUNTER}


@app.put("/items/{item_id}")
def update_item(item_id: int, update: ItemUpdate):
    if item_id >= len(ITEMS):
        return JSONResponse(status_code=200, content={"error": "not found"})
    ITEMS[item_id] = {"id": item_id, "name": update.name}
    return ITEMS[item_id]


@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    if item_id >= len(ITEMS):
        return {"error": "not found"}
    ITEMS.pop(item_id)
    return {"deleted": True}


@app.get("/divide")
def divide(a: int, b: int):
    return {"result": a / b}


@app.get("/slow-sync")
def slow_sync():
    time.sleep(0.5)
    return {"status": "done"}
