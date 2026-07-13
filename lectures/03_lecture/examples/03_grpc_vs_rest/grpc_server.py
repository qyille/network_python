"""
03_grpc_vs_rest / grpc_server.py — gRPC-версия Bookstore.

Запуск:
    python grpc_server.py
"""

from concurrent import futures
import logging

import grpc
import bookstore_pb2
import bookstore_pb2_grpc

logger = logging.getLogger(__name__)

# In-memory storage (такая же, как в REST-версии)
BOOKS: list[dict] = []
NEXT_ID = 1


class BookstoreServicer(bookstore_pb2_grpc.BookstoreServicer):

    def ListBooks(self, request, context):
        resp = bookstore_pb2.ListBooksResponse()
        for b in BOOKS:
            if request.HasField("year_filter") and b["year"] != request.year_filter:
                continue
            resp.books.append(bookstore_pb2.Book(**b))
        return resp

    def GetBook(self, request, context):
        for b in BOOKS:
            if b["id"] == request.id:
                return bookstore_pb2.Book(**b)
        context.abort(grpc.StatusCode.NOT_FOUND, "Book not found")

    def CreateBook(self, request, context):
        global NEXT_ID
        book = {
            "id": NEXT_ID,
            "title": request.title,
            "author": request.author,
            "year": request.year,
            "isbn": request.isbn,
            "price": request.price,
        }
        NEXT_ID += 1
        BOOKS.append(book)
        return bookstore_pb2.Book(**book)

    def UpdateBook(self, request, context):
        for i, b in enumerate(BOOKS):
            if b["id"] == request.id:
                updated = {
                    "id": request.id,
                    "title": request.title,
                    "author": request.author,
                    "year": request.year,
                    "isbn": request.isbn,
                    "price": request.price,
                }
                BOOKS[i] = updated
                return bookstore_pb2.Book(**updated)
        context.abort(grpc.StatusCode.NOT_FOUND, "Book not found")

    def DeleteBook(self, request, context):
        for i, b in enumerate(BOOKS):
            if b["id"] == request.id:
                BOOKS.pop(i)
                return bookstore_pb2.DeleteBookResponse(success=True)
        context.abort(grpc.StatusCode.NOT_FOUND, "Book not found")


def serve(port: int = 50053):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    bookstore_pb2_grpc.add_BookstoreServicer_to_server(BookstoreServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("gRPC Bookstore запущен на порту %s", port)
    return server


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    serve().wait_for_termination()
