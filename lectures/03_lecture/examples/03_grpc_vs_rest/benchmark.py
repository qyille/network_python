#!/usr/bin/env python
"""
03_grpc_vs_rest / benchmark.py — Сравнение gRPC и REST.

Запускает in-process сервер gRPC и uvicorn-подпроцесс для REST,
выполняет одинаковые CRUD-операции и замеряет время / размер.

ОБА протокола работают через сеть (localhost) — честное сравнение.

Запуск:
    python benchmark.py
"""

import asyncio
import json as _json
import logging
import subprocess
import time
import sys
from pathlib import Path

import httpx

from grpc_server import serve as grpc_serve
from grpc_client import GrpcBookClient

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Управление серверами
# ═══════════════════════════════════════════════════════════════════════════════

HERE = Path(__file__).parent


class RestServerManager:
    """Запускает uvicorn как подпроцесс и управляет его жизнью."""

    def __init__(self, port: int = 8001):
        self.port = port
        self._proc: subprocess.Popen | None = None
        self._client: httpx.AsyncClient | None = None

    async def start(self):
        self._proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "rest_server:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
                "--log-level",
                "warning",
            ],
            cwd=str(HERE),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._client = httpx.AsyncClient(base_url=f"http://127.0.0.1:{self.port}")
        # ждём, пока сервер поднимется
        for _ in range(50):
            try:
                await self._client.get("/books", timeout=1)
                break
            except (httpx.ConnectError, httpx.ReadTimeout):
                await asyncio.sleep(0.1)
        else:
            raise RuntimeError("REST-сервер не поднялся за 5 секунд")

    async def reset(self):
        await self._client.post("/reset", timeout=5)

    async def stop(self):
        if self._proc:
            self._proc.terminate()
            self._proc.wait(timeout=5)
        if self._client:
            await self._client.aclose()


class RestHttpClient:
    """REST-клиент через реальный HTTP (localhost).
    Возвращает (data, req_size, resp_size)."""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def list_books(self):
        resp = await self._client.get("/books", timeout=5)
        return resp.json(), 0, len(resp.content)

    async def get_book(self, book_id: int):
        resp = await self._client.get(f"/books/{book_id}", timeout=5)
        return resp.json(), 0, len(resp.content)

    async def create_book(self, book: dict):
        req_bytes = _json.dumps(book).encode("utf-8")
        resp = await self._client.post("/books", json=book, timeout=5)
        return resp.json(), len(req_bytes), len(resp.content)

    async def update_book(self, book_id: int, book: dict):
        req_bytes = _json.dumps(book).encode("utf-8")
        resp = await self._client.put(f"/books/{book_id}", json=book, timeout=5)
        return resp.json(), len(req_bytes), len(resp.content)

    async def delete_book(self, book_id: int):
        resp = await self._client.delete(f"/books/{book_id}", timeout=5)
        return resp.status_code, 0, len(resp.content)


# ═══════════════════════════════════════════════════════════════════════════════
# Данные
# ═══════════════════════════════════════════════════════════════════════════════

_AUTHORS = [
    "Толстой",
    "Достоевский",
    "Булгаков",
    "Пушкин",
    "Гоголь",
    "Чехов",
    "Тургенев",
    "Гончаров",
    "Лермонтов",
    "Солженицын",
]

SAMPLE_BOOKS: list[dict] = []
for i in range(200):
    SAMPLE_BOOKS.append(
        {
            "title": f"Книга {i + 1}",
            "author": _AUTHORS[i % len(_AUTHORS)],
            "year": 1800 + (i % 200),
            "isbn": f"978-5-99999-{i:04d}-{i % 9 + 1}",
            "price": round(100.0 + i * 5.5, 2),
        }
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Бенчмарк
# ═══════════════════════════════════════════════════════════════════════════════


async def _run_rest_benchmark(rest: RestServerManager):
    """REST-бенчмарк (через реальный HTTP)."""
    results = {}
    client = RestHttpClient(rest._client)

    for op in ("create", "list", "get"):
        op_fn = getattr(client, op + "_book" if op != "list" else "list_books")
        times = []
        req_sizes = []
        resp_sizes = []

        if op == "list":
            t0 = time.perf_counter()
            data, req_b, resp_b = await op_fn()
            elapsed = time.perf_counter() - t0
            times.append(elapsed)
            req_sizes.append(req_b)
            resp_sizes.append(resp_b)
        elif op == "create":
            await rest.reset()
            for book in SAMPLE_BOOKS:
                t0 = time.perf_counter()
                data, req_b, resp_b = await client.create_book(book)
                elapsed = time.perf_counter() - t0
                times.append(elapsed)
                req_sizes.append(req_b)
                resp_sizes.append(resp_b)
        else:  # get
            for i in range(1, len(SAMPLE_BOOKS) + 1):
                t0 = time.perf_counter()
                data, req_b, resp_b = await client.get_book(i)
                elapsed = time.perf_counter() - t0
                times.append(elapsed)
                req_sizes.append(req_b)
                resp_sizes.append(resp_b)

        results[op] = {
            "avg_time_ms": sum(times) / len(times) * 1000,
            "avg_req_bytes": sum(req_sizes) / len(req_sizes),
            "avg_resp_bytes": sum(resp_sizes) / len(resp_sizes),
            "count": len(SAMPLE_BOOKS) if op != "list" else None,
        }

    return results


def reset_state():
    """Сбрасывает in-memory состояние gRPC-сервера."""
    import grpc_server as gs

    gs.BOOKS.clear()
    gs.NEXT_ID = 1


def _run_grpc_benchmark():
    """gRPC-бенчмарк (через реальный TCP, localhost)."""
    results = {}
    client = GrpcBookClient()

    for op in ("create", "list", "get"):
        op_fn = getattr(client, op + "_book" if op != "list" else "list_books")
        times = []
        req_sizes = []
        resp_sizes = []

        if op == "list":
            t0 = time.perf_counter()
            data, req_b, resp_b = op_fn()
            elapsed = time.perf_counter() - t0
            times.append(elapsed)
            req_sizes.append(req_b)
            resp_sizes.append(resp_b)
        elif op == "create":
            reset_state()
            for book in SAMPLE_BOOKS:
                t0 = time.perf_counter()
                data, req_b, resp_b = client.create_book(book)
                elapsed = time.perf_counter() - t0
                times.append(elapsed)
                req_sizes.append(req_b)
                resp_sizes.append(resp_b)
        else:  # get
            for i in range(1, len(SAMPLE_BOOKS) + 1):
                t0 = time.perf_counter()
                data, req_b, resp_b = client.get_book(i)
                elapsed = time.perf_counter() - t0
                times.append(elapsed)
                req_sizes.append(req_b)
                resp_sizes.append(resp_b)

        results[op] = {
            "avg_time_ms": sum(times) / len(times) * 1000,
            "avg_req_bytes": sum(req_sizes) / len(req_sizes),
            "avg_resp_bytes": sum(resp_sizes) / len(resp_sizes),
            "count": len(SAMPLE_BOOKS) if op != "list" else None,
        }

    client.channel.close()
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# Вывод результатов
# ═══════════════════════════════════════════════════════════════════════════════


def print_results(results: dict):
    """Форматированный вывод таблицы сравнения — суммарно по каждой операции."""

    print()
    print("=" * 88)
    print("  📊 Сравнение gRPC vs REST — Bookstore (200 книг)")
    print("  Оба протокола — через реальную сеть (localhost)")
    print("=" * 88)

    # Суммарные значения по каждой операции (avg × количество вызовов)
    counts = {"create": len(SAMPLE_BOOKS), "list": 1, "get": len(SAMPLE_BOOKS)}
    totals_op = {"rest": {}, "grpc": {}}
    for label, res in [("rest", results["rest"]), ("grpc", results["grpc"])]:
        for op in ["create", "list", "get"]:
            cnt = counts[op]
            totals_op[label][op] = {
                "time_ms": res[op]["avg_time_ms"] * cnt,
                "req_bytes": res[op]["avg_req_bytes"] * cnt,
                "resp_bytes": res[op]["avg_resp_bytes"] * cnt,
            }
            totals_op[label][op]["total_bytes"] = (
                totals_op[label][op]["req_bytes"] + totals_op[label][op]["resp_bytes"]
            )

    # ---------- Таблица по операциям (суммарно) ----------
    print()
    print(
        f"{'Операция':<12} {'Метрика':<30} {'REST (JSON)':<18} {'gRPC':<18} {'Разница':<12}"
    )
    print("-" * 92)

    for op in ["create", "list", "get"]:
        op_label = {"create": "CREATE", "list": "LIST", "get": "GET"}[op]
        r = totals_op["rest"][op]
        g = totals_op["grpc"][op]

        # время — суммарно
        diff_time = (r["time_ms"] - g["time_ms"]) / r["time_ms"] * 100
        print(
            f"{op_label:<12} {'Суммарное время (мс)':<30} {r['time_ms']:<18.2f} {g['time_ms']:<18.2f} {diff_time:<+10.0f}%"
        )
        # байты всего
        diff_total = (r["total_bytes"] - g["total_bytes"]) / r["total_bytes"] * 100
        print(
            f"{'':12} {'Всего байт (req+resp)':<30} {r['total_bytes']:<18,.0f} {g['total_bytes']:<18,.0f} {diff_total:<+10.0f}%"
        )
        # в т.ч. ответ
        diff_resp = (r["resp_bytes"] - g["resp_bytes"]) / r["resp_bytes"] * 100
        print(
            f"{'':12} {'в т.ч. тело ответа':<30} {r['resp_bytes']:<18,.0f} {g['resp_bytes']:<18,.0f} {diff_resp:<+10.0f}%"
        )
        # в т.ч. запрос
        diff_req = (
            (r["req_bytes"] - g["req_bytes"]) / r["req_bytes"] * 100
            if r["req_bytes"]
            else 0
        )
        print(
            f"{'':12} {'в т.ч. тело запроса':<30} {r['req_bytes']:<18,.0f} {g['req_bytes']:<18,.0f} {diff_req:<+10.0f}%"
        )
        print()

    # ---------- ИТОГО за весь бенчмарк ----------
    print("-" * 92)
    print("\n📈 ИТОГО ЗА ВЕСЬ БЕНЧМАРК:\n")

    grand = {
        "rest": {"req": 0, "resp": 0, "time": 0},
        "grpc": {"req": 0, "resp": 0, "time": 0},
    }
    for label in ("rest", "grpc"):
        for op in ("create", "list", "get"):
            t = totals_op[label][op]
            grand[label]["req"] += t["req_bytes"]
            grand[label]["resp"] += t["resp_bytes"]
            grand[label]["time"] += t["time_ms"]

    for t in grand.values():
        t["total"] = t["req"] + t["resp"]

    rt = grand["rest"]
    gt = grand["grpc"]

    print(f"  {'Метрика':<30} {'REST (JSON)':<18} {'gRPC':<18} {'Разница':<12}")
    print(f"  {'-' * 78}")
    print(
        f"  {'Запросы':<30} {rt['req']:<18,.0f} {gt['req']:<18,.0f} "
        f"{(rt['req'] - gt['req']) / rt['req'] * 100:<+10.0f}%"
    )
    print(
        f"  {'Ответы':<30} {rt['resp']:<18,.0f} {gt['resp']:<18,.0f} "
        f"{(rt['resp'] - gt['resp']) / rt['resp'] * 100:<+10.0f}%"
    )
    print(
        f"  {'ВСЕГО байт':<30} {rt['total']:<18,.0f} {gt['total']:<18,.0f} "
        f"{(rt['total'] - gt['total']) / rt['total'] * 100:<+10.0f}%"
    )
    print(
        f"  {'ВСЕГО время (мс)':<30} {rt['time']:<18,.2f} {gt['time']:<18,.2f} "
        f"{(rt['time'] - gt['time']) / rt['time'] * 100:<+10.0f}%"
    )

    comp = rt["total"] / gt["total"]
    speed = rt["time"] / gt["time"]
    print(
        f"\n  🔑 ИТОГО: gRPC передал в {comp:.1f}x меньше данных"
        + (f" и в {speed:.1f}x быстрее" if gt["time"] > 0 else "")
    )
    print()

    print("=" * 88)
    print("📌 Почему gRPC быстрее и компактнее:")
    print("  1. Protobuf (C-ext) сериализует быстрее, чем json (Python-код)")
    print("  2. HTTP/2 мультиплексирует запросы — меньше latency при 200+ вызовах")
    print("  3. Бинарный формат компактнее — меньше данных по сети")
    print("  4. Varint для чисел эффективнее ASCII-цифр в JSON")
    print("  5. Нет повторения имён полей в каждом объекте")
    print()


async def main():
    logging.basicConfig(level=logging.WARNING)
    results = {"rest": {}, "grpc": {}}

    # REST — запускаем uvicorn
    rest_mgr = RestServerManager(port=8001)
    await rest_mgr.start()
    try:
        results["rest"] = await _run_rest_benchmark(rest_mgr)
    finally:
        await rest_mgr.stop()

    # gRPC — запускаем in-process сервер
    grpc_server = grpc_serve(port=50053)
    try:
        results["grpc"] = _run_grpc_benchmark()
    finally:
        grpc_server.stop(grace=1)

    print_results(results)


if __name__ == "__main__":
    asyncio.run(main())
