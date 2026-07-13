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
    """Доменная модель категории. Возвращается в ответах."""

    id: int
    name: str = Field(min_length=1, max_length=50)


class CategoryCreate(BaseModel):
    """Модель для создания категории (без id, лишние поля запрещены)."""

    name: str = Field(min_length=1, max_length=50)

    model_config = {"extra": "forbid"}


class Book(BaseModel):
    """Доменная модель книги. Возвращается в ответах GET/PUT."""

    id: int
    title: str = Field(min_length=1, max_length=100)
    author: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1900, le=2025)
    isbn: str
    price: float = Field(gt=0)
    category_id: Optional[int] = None


class BookCreate(BaseModel):
    """Модель для создания/обновления книги (без id — сервер сгенерирует)."""

    title: str = Field(min_length=1, max_length=100)
    author: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1900, le=2025)
    isbn: str
    price: float = Field(gt=0)
    category_id: Optional[int] = None


# ═══════════════════════════════════════════════════════════
# ИСКЛЮЧЕНИЯ
# ═══════════════════════════════════════════════════════════


class BookNotFoundException(HTTPException):
    """404 — книга не найдена."""

    # TODO: реализуйте


class DuplicateIsbnException(HTTPException):
    """409 — ISBN уже существует."""

    # TODO: реализуйте


# ═══════════════════════════════════════════════════════════
# ПРИЛОЖЕНИЕ
# ═══════════════════════════════════════════════════════════

app = FastAPI(title="Bookstore API")

# Хранилище
BOOKS: list[dict] = []
CATEGORIES: list[dict] = []


# ═══════════════════════════════════════════════════════════
# КАТЕГОРИИ
# ═══════════════════════════════════════════════════════════


@app.get("/categories")
def list_categories():
    """GET /categories — список всех категорий."""
    # TODO: реализуйте
    raise NotImplementedError


@app.post("/categories", status_code=201)
def create_category(category: CategoryCreate):
    """POST /categories — создать категорию."""
    # TODO: реализуйте
    raise NotImplementedError


# ═══════════════════════════════════════════════════════════
# CRUID КНИГ
# ═══════════════════════════════════════════════════════════


@app.get("/books")
def list_books(category_id: Optional[int] = None, year: Optional[int] = None):
    """GET /books — список книг. Опциональная фильтрация по category_id и year."""
    # TODO: реализуйте
    raise NotImplementedError


@app.get("/books/search")
def search_books(query: str):
    """GET /books/search?query=... — поиск по title и author (case-insensitive)."""
    # TODO: реализуйте
    raise NotImplementedError


@app.get("/books/{book_id}")
def get_book(book_id: int):
    """GET /books/{id} — одна книга."""
    # TODO: реализуйте
    raise NotImplementedError


@app.post("/books", status_code=201)
def create_book(book: BookCreate):
    """POST /books — создать книгу.

    Проверять уникальность ISBN. Если дубликат — DuplicateIsbnException.
    """
    # TODO: реализуйте
    raise NotImplementedError


@app.put("/books/{book_id}")
def update_book(book_id: int, book: BookCreate):
    """PUT /books/{id} — полностью обновить книгу."""
    # TODO: реализуйте
    raise NotImplementedError


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    """DELETE /books/{id} — удалить книгу."""
    # TODO: реализуйте
    raise NotImplementedError
