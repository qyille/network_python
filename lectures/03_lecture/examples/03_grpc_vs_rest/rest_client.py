"""
03_grpc_vs_rest / rest_client.py — REST-клиент для бенчмарка.

Использует httpx для HTTP-запросов к FastAPI-серверу.
"""

import httpx


class RestBookClient:
    """Клиент для REST Bookstore (FastAPI)."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")

    def list_books(self):
        resp = httpx.get(f"{self.base_url}/books", timeout=5)
        resp.raise_for_status()
        return resp.json(), len(resp.content)

    def get_book(self, book_id: int):
        resp = httpx.get(f"{self.base_url}/books/{book_id}", timeout=5)
        resp.raise_for_status()
        return resp.json(), len(resp.content)

    def create_book(self, book: dict):
        resp = httpx.post(f"{self.base_url}/books", json=book, timeout=5)
        resp.raise_for_status()
        return resp.json(), len(resp.content)

    def update_book(self, book_id: int, book: dict):
        resp = httpx.put(f"{self.base_url}/books/{book_id}", json=book, timeout=5)
        resp.raise_for_status()
        return resp.json(), len(resp.content)

    def delete_book(self, book_id: int):
        resp = httpx.delete(f"{self.base_url}/books/{book_id}", timeout=5)
        return resp.status_code, 0

    def clear(self):
        """Удаляет все книги (для сброса между замерами)."""
        books, _ = self.list_books()
        for b in books:
            self.delete_book(b["id"])
