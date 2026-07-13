"""
03_grpc_vs_rest / rest_server.py — REST-версия Bookstore (FastAPI).

Запуск:
    uvicorn rest_server:app --port 8000
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Bookstore REST")

# In-memory storage
BOOKS: list[dict] = []
NEXT_ID = 1


@app.post("/reset")
def reset():
    global NEXT_ID
    BOOKS.clear()
    NEXT_ID = 1
    return {"status": "ok"}


class BookIn(BaseModel):
    title: str
    author: str
    year: int
    isbn: str
    price: float


class BookOut(BaseModel):
    id: int
    title: str
    author: str
    year: int
    isbn: str
    price: float


@app.get("/books")
def list_books(year: Optional[int] = None):
    if year is not None:
        return [b for b in BOOKS if b["year"] == year]
    return BOOKS


@app.get("/books/{book_id}")
def get_book(book_id: int):
    for b in BOOKS:
        if b["id"] == book_id:
            return b
    raise HTTPException(status_code=404, detail="Book not found")


@app.post("/books", status_code=201)
def create_book(book: BookIn):
    global NEXT_ID
    new = book.model_dump()
    new["id"] = NEXT_ID
    NEXT_ID += 1
    BOOKS.append(new)
    return new


@app.put("/books/{book_id}")
def update_book(book_id: int, book: BookIn):
    for i, b in enumerate(BOOKS):
        if b["id"] == book_id:
            updated = book.model_dump()
            updated["id"] = book_id
            BOOKS[i] = updated
            return updated
    raise HTTPException(status_code=404, detail="Book not found")


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    for i, b in enumerate(BOOKS):
        if b["id"] == book_id:
            BOOKS.pop(i)
            return
    raise HTTPException(status_code=404, detail="Book not found")
