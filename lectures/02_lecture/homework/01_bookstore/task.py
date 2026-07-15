"""
01_bookstore — CRUD API для книжного магазина 📚

Спроектируйте REST API для управления каталогом книг.

Спецификация эндпоинтов (ничего не менять — тесты завязаны на них):

    GET    /books              — список книг (с опциональной фильтрацией)
    GET    /books/{id}         — одна книга по id
    POST   /books              — создать книгу
    PUT    /books/{id}         — полностью обновить книгу
    DELETE /books/{id}         — удалить книгу
    GET    /books/search       — поиск книг по названию или автору

    # Дополнительно — категории
    GET    /categories         — список категорий
    POST   /categories         — создать категорию

Требования к реализации:
    1. Используйте FastAPI + Pydantic
    2. Храните данные в памяти (глобальный список/словарь)
    3. Правильные HTTP-статусы:
        - 200 — успешный GET, PUT
        - 201 — успешный POST
        - 204 — успешный DELETE
        - 404 — ресурс не найден
        - 409 — конфликт (например, дубликат)
        - 422 — невалидные данные (Pydantic сам это делает)
    4. Валидация полей через Pydantic Field:
        - title:  не пустой, до 100 символов
        - author: не пустой, до 100 символов
        - year:   ≥ 0, до 2025
        - isbn:   строка 10 или 13 цифр (978-5-xxx...)
        - price:  > 0
        - category_id: опционально, ссылка на категорию
    5. Кастомная обработка ошибок:
        - BookNotFoundException → 404 c {"detail": "Book not found", "code": "NOT_FOUND"}
        - DuplicateIsbnException → 409 c {"detail": "...", "code": "DUPLICATE_ISBN"}
    6. Поиск /books/search?query=... — ищет по title и author (case-insensitive)
    7. Фильтрация GET /books?category_id=N&year=2024
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional

# ═══════════════════════════════════════════════════════════
# МОДЕЛИ
# ═══════════════════════════════════════════════════════════


class Category(BaseModel):
    """Доменная модель категории."""
    id: int
    name: str = Field(min_length=1, max_length=50)


class CategoryCreate(BaseModel):
    """Модель для создания категории."""
    name: str = Field(min_length=1, max_length=50)

    model_config = {"extra": "forbid"}


class Book(BaseModel):
    """Доменная модель книги."""
    id: int
    title: str = Field(min_length=1, max_length=100)
    author: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=0, le=2025)
    isbn: str
    price: float = Field(gt=0)
    category_id: Optional[int] = None


class BookCreate(BaseModel):
    """Модель для создания/обновления книги."""
    title: str = Field(min_length=1, max_length=100)
    author: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=0, le=2025)
    isbn: str
    price: float = Field(gt=0)
    category_id: Optional[int] = None

    model_config = {"extra": "forbid"}


# ═══════════════════════════════════════════════════════════
# ИСКЛЮЧЕНИЯ
# ═══════════════════════════════════════════════════════════


class BookNotFoundException(Exception):
    """Книга не найдена."""
    pass


class DuplicateIsbnException(Exception):
    """Дубликат ISBN."""

    def __init__(self, isbn: str):
        self.isbn = isbn


# ═══════════════════════════════════════════════════════════
# ПРИЛОЖЕНИЕ
# ═══════════════════════════════════════════════════════════

app = FastAPI(title="Bookstore API")

# Хранилище
BOOKS: list[dict] = []
CATEGORIES: list[dict] = []
next_book_id = 1
next_category_id = 1


# ═══════════════════════════════════════════════════════════
# ОБРАБОТЧИКИ ИСКЛЮЧЕНИЙ
# ═══════════════════════════════════════════════════════════

@app.exception_handler(BookNotFoundException)
async def book_not_found_handler(request: Request, exc: BookNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": "Book not found", "code": "NOT_FOUND"}
    )


@app.exception_handler(DuplicateIsbnException)
async def duplicate_isbn_handler(request: Request, exc: DuplicateIsbnException):
    return JSONResponse(
        status_code=409,
        content={
            "detail": f"Book with ISBN {exc.isbn} already exists",
            "code": "DUPLICATE_ISBN"
        }
    )


# ═══════════════════════════════════════════════════════════
# КАТЕГОРИИ
# ═══════════════════════════════════════════════════════════


@app.get("/categories")
def list_categories():
    """GET /categories — список всех категорий."""
    return CATEGORIES


@app.post("/categories", status_code=201)
def create_category(category: CategoryCreate):
    """POST /categories — создать категорию."""
    global next_category_id

    new_category = {
        "id": next_category_id,
        "name": category.name
    }
    CATEGORIES.append(new_category)
    next_category_id += 1

    return new_category


# ═══════════════════════════════════════════════════════════
# CRUD КНИГ
# ═══════════════════════════════════════════════════════════


@app.get("/books")
def list_books(category_id: Optional[int] = None, year: Optional[int] = None):
    """GET /books — список книг с фильтрацией."""
    result = BOOKS.copy()

    if category_id is not None:
        result = [book for book in result if book.get("category_id") == category_id]

    if year is not None:
        result = [book for book in result if book.get("year") == year]

    return result


@app.get("/books/search")
def search_books(query: str):
    """GET /books/search?query=... — поиск по title и author."""
    query_lower = query.lower()
    result = [
        book for book in BOOKS
        if query_lower in book["title"].lower() or query_lower in book["author"].lower()
    ]
    return result


@app.get("/books/{book_id}")
def get_book(book_id: int):
    """GET /books/{id} — одна книга."""
    for book in BOOKS:
        if book["id"] == book_id:
            return book

    raise BookNotFoundException()


@app.post("/books", status_code=201)
def create_book(book: BookCreate):
    """POST /books — создать книгу."""
    global next_book_id

    if any(b["isbn"] == book.isbn for b in BOOKS):
        raise DuplicateIsbnException(book.isbn)

    new_book = book.model_dump()
    new_book["id"] = next_book_id
    BOOKS.append(new_book)
    next_book_id += 1

    return new_book


@app.put("/books/{book_id}")
def update_book(book_id: int, book: BookCreate):
    """PUT /books/{id} — полностью обновить книгу."""
    for i, existing_book in enumerate(BOOKS):
        if existing_book["id"] == book_id:
            if any(b["isbn"] == book.isbn and b["id"] != book_id for b in BOOKS):
                raise DuplicateIsbnException(book.isbn)

            updated_book = book.model_dump()
            updated_book["id"] = book_id
            BOOKS[i] = updated_book
            return updated_book

    raise BookNotFoundException()


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    """DELETE /books/{id} — удалить книгу."""
    for i, book in enumerate(BOOKS):
        if book["id"] == book_id:
            BOOKS.pop(i)
            return

    raise BookNotFoundException()
