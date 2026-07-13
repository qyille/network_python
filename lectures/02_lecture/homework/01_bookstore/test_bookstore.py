"""Тесты к ДЗ 1: Bookstore API."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from starlette.testclient import TestClient

from task import app

client = TestClient(app)

# Счётчик для генерации уникальных ISBN в каждом тесте
_isbn_counter = 0


def _next_isbn():
    """Генерирует уникальный 10-значный ISBN."""
    global _isbn_counter
    _isbn_counter += 1
    return f"{_isbn_counter:010d}"


# ═══════════════════════════════════════════════════════════
# Категории
# ═══════════════════════════════════════════════════════════


class TestCategories:
    def test_create_category(self):
        resp = client.post("/categories", json={"name": "Фантастика"})
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["name"] == "Фантастика"

    def test_list_categories(self):
        resp = client.get("/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_category_invalid_name(self):
        resp = client.post("/categories", json={"name": ""})
        assert resp.status_code == 422

    def test_category_extra_field(self):
        """Лишние поля должны reject'иться."""
        resp = client.post("/categories", json={"name": "OK", "extra": "no"})
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════
# CRUD книг
# ═══════════════════════════════════════════════════════════


def _make_book(
    title="Война и мир", author="Лев Толстой", year=1869, price=599.99, isbn=None
):
    """Создать словарь с данными книги."""
    return {
        "title": title,
        "author": author,
        "year": year,
        "isbn": isbn or _next_isbn(),
        "price": price,
    }


class TestCreateBook:
    def test_create_book(self):
        resp = client.post("/books", json=_make_book())
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Война и мир"
        assert "id" in data

    def test_create_duplicate_isbn(self):
        isbn = _next_isbn()
        book = _make_book(isbn=isbn)
        client.post("/books", json=book)
        resp = client.post("/books", json=book)
        assert resp.status_code == 409
        data = resp.json()
        assert "code" in data
        assert data["code"] == "DUPLICATE_ISBN"

    def test_create_book_missing_field(self):
        resp = client.post("/books", json={"title": "only"})
        assert resp.status_code == 422

    def test_create_book_negative_year(self):
        book = _make_book(year=-1)
        resp = client.post("/books", json=book)
        assert resp.status_code == 422

    def test_create_book_negative_price(self):
        book = _make_book(price=-10)
        resp = client.post("/books", json=book)
        assert resp.status_code == 422


class TestGetBooks:
    def test_list_books(self):
        resp = client.get("/books")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_get_book_by_id(self):
        create = client.post("/books", json=_make_book())
        book_id = create.json()["id"]
        resp = client.get(f"/books/{book_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Война и мир"

    def test_get_book_not_found(self):
        resp = client.get("/books/999999")
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data

    def test_get_negative_id(self):
        resp = client.get("/books/-1")
        assert resp.status_code == 404


class TestSearchBooks:
    def test_search_by_title(self):
        client.post(
            "/books",
            json=_make_book(
                title="Война и мир",
                author="Лев Толстой",
            ),
        )
        resp = client.get("/books/search", params={"query": "война"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        assert any("Война и мир" in b["title"] for b in data)

    def test_search_by_author(self):
        client.post("/books", json=_make_book(author="Лев Толстой"))
        resp = client.get("/books/search", params={"query": "толстой"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0

    def test_search_no_query(self):
        """Без query → 422 (обязательный параметр)."""
        resp = client.get("/books/search")
        assert resp.status_code == 422

    def test_search_empty_result(self):
        resp = client.get("/books/search", params={"query": "zzznonexistent"})
        assert resp.status_code == 200
        assert resp.json() == []


class TestFilterBooks:
    def test_filter_by_year(self):
        client.post("/books", json=_make_book(year=1866))
        resp = client.get("/books", params={"year": 1866})
        assert resp.status_code == 200
        data = resp.json()
        assert any(b["year"] == 1866 for b in data)

    def test_filter_no_match(self):
        resp = client.get("/books", params={"year": 2100})
        assert resp.status_code == 200
        assert resp.json() == []


class TestUpdateBook:
    def test_update_book(self):
        isbn = _next_isbn()
        create = client.post("/books", json=_make_book(isbn=isbn))
        book_id = create.json()["id"]
        updated = _make_book(
            title="Война и мир (обновлённое)",
            year=1870,
            price=699.99,
            isbn=_next_isbn(),
        )
        resp = client.put(f"/books/{book_id}", json=updated)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Война и мир (обновлённое)"

    def test_update_not_found(self):
        resp = client.put("/books/999999", json=_make_book())
        assert resp.status_code == 404


class TestDeleteBook:
    def test_delete_book(self):
        create = client.post("/books", json=_make_book())
        book_id = create.json()["id"]
        resp = client.delete(f"/books/{book_id}")
        assert resp.status_code == 204

        # Проверяем что удалилась
        get = client.get(f"/books/{book_id}")
        assert get.status_code == 404

    def test_delete_not_found(self):
        resp = client.delete("/books/999999")
        assert resp.status_code == 404

    def test_delete_twice(self):
        create = client.post("/books", json=_make_book())
        book_id = create.json()["id"]
        client.delete(f"/books/{book_id}")
        resp = client.delete(f"/books/{book_id}")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════
# Content-Type и заголовки
# ═══════════════════════════════════════════════════════════


class TestHeaders:
    def test_content_type_json(self):
        resp = client.get("/books")
        assert resp.headers["content-type"] == "application/json"

    def test_error_response_format(self):
        """Ошибки должны содержать detail и code."""
        resp = client.get("/books/999999")
        data = resp.json()
        assert "detail" in data
        assert "code" in data
