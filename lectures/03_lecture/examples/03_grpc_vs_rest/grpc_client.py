"""
03_grpc_vs_rest / grpc_client.py — gRPC-клиент для бенчмарка.
"""

import grpc
import bookstore_pb2
import bookstore_pb2_grpc


class GrpcBookClient:
    """Клиент для gRPC Bookstore."""

    def __init__(self, target: str = "localhost:50053"):
        self.channel = grpc.insecure_channel(target)
        self.stub = bookstore_pb2_grpc.BookstoreStub(self.channel)

    def list_books(self):
        req = bookstore_pb2.ListBooksRequest()
        resp = self.stub.ListBooks(req)
        req_bytes = len(req.SerializeToString())
        resp_bytes = len(resp.SerializeToString())
        return [{"id": b.id, "title": b.title, "author": b.author,
                  "year": b.year, "isbn": b.isbn, "price": b.price}
                for b in resp.books], req_bytes, resp_bytes

    def get_book(self, book_id: int):
        req = bookstore_pb2.GetBookRequest(id=book_id)
        resp = self.stub.GetBook(req)
        return {"id": resp.id, "title": resp.title, "author": resp.author,
                "year": resp.year, "isbn": resp.isbn, "price": resp.price}, \
               len(req.SerializeToString()), len(resp.SerializeToString())

    def create_book(self, book: dict):
        req = bookstore_pb2.CreateBookRequest(**book)
        resp = self.stub.CreateBook(req)
        return {"id": resp.id, "title": resp.title}, \
               len(req.SerializeToString()), len(resp.SerializeToString())

    def update_book(self, book_id: int, book: dict):
        req = bookstore_pb2.UpdateBookRequest(id=book_id, **book)
        resp = self.stub.UpdateBook(req)
        return {"id": resp.id, "title": resp.title}, \
               len(req.SerializeToString()), len(resp.SerializeToString())

    def delete_book(self, book_id: int):
        req = bookstore_pb2.DeleteBookRequest(id=book_id)
        resp = self.stub.DeleteBook(req)
        return 204, len(req.SerializeToString()), len(resp.SerializeToString())

    def clear(self):
        """Удаляет все книги."""
        books, _, _ = self.list_books()
        for b in books:
            self.delete_book(b["id"])
