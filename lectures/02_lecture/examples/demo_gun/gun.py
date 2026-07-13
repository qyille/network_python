"""
demo_gun / gun.py — нагрузочная «пушка» для сравнения FastAPI vs Flask.

Использует in-process тестовые клиенты (ASGITransport / Flask.test_client()),
чтобы не занимать порты и не зависеть от внешних серверов.

Запуск:
    python gun.py              # протестировать всё
    python gun.py --app fastapi  # только FastAPI
    python gun.py -n 300 -c 20   # 300 запросов, 20 конкурентных
"""

import argparse
import asyncio
import time
from dataclasses import dataclass, field

from apps.fastapi_app import app as fastapi_app
from apps.flask_app import app as flask_app


# ---------------------------------------------------------------------------
# Транспорты (in-process, без портов)
# ---------------------------------------------------------------------------


def make_fastapi_transport():
    """FastAPI через ASGITransport — полностью асинхронный."""
    from httpx import ASGITransport

    return ASGITransport(app=fastapi_app)


def make_flask_client():
    """Flask через Werkzeug TestClient — синхронный."""
    return flask_app.test_client()


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class Stats:
    """Статистика по серии запросов."""

    total: int = 0
    ok: int = 0
    errors: int = 0
    times: list[float] = field(default_factory=list)

    @property
    def avg(self) -> float:
        return sum(self.times) / len(self.times) if self.times else 0.0

    def p95(self) -> float:
        if not self.times:
            return 0.0
        s = sorted(self.times)
        return s[int(len(s) * 0.95)]

    def p99(self) -> float:
        if not self.times:
            return 0.0
        s = sorted(self.times)
        return s[int(len(s) * 0.99)]

    @property
    def rps(self) -> float:
        total_time = sum(self.times)
        return len(self.times) / total_time if total_time else 0.0


# ---------------------------------------------------------------------------
# Эндпоинты
# ---------------------------------------------------------------------------
ENDPOINTS = {
    "GET  /items": {"method": "GET", "path": "/items"},
    "GET  /items/1": {"method": "GET", "path": "/items/1"},
    "POST /items": {
        "method": "POST",
        "path": "/items",
        "body": {"name": "X", "price": 999},
    },
    "GET  /items/sync": {"method": "GET", "path": "/items/sync"},
}


# ---------------------------------------------------------------------------
# «Стрельба» по FastAPI (асинхронно)
# ---------------------------------------------------------------------------
async def shoot_fastapi(n: int, concurrency: int) -> dict[str, Stats]:
    """N запросов к FastAPI через ASGITransport с заданным concurrency.

    FastAPI async: ВСЕ concurrent запросов обрабатываются в одном event loop
    параллельно. Если 200 запросов приходят одновременно, все 200 asyncio.sleep()
    запускаются одновременно — все 200 завершатся через ~50ms.
    """
    import httpx

    transport = make_fastapi_transport()
    results: dict[str, Stats] = {}

    for label, ep in ENDPOINTS.items():
        print(f"  fastapi: {label} ...", end=" ", flush=True)

        limits = httpx.Limits(max_connections=concurrency)
        async with httpx.AsyncClient(
            base_url="http://test", transport=transport, limits=limits, timeout=10
        ) as client:
            stats = Stats()

            async def fire() -> tuple[bool, float]:
                try:
                    t0 = time.perf_counter()
                    if ep["method"] == "GET":
                        r = await client.get(ep["path"])
                    else:
                        r = await client.post(ep["path"], json=ep.get("body"))
                    elapsed = (time.perf_counter() - t0) * 1000  # ms
                    return r.status_code < 500, elapsed
                except Exception:
                    return False, 0.0

            # Запускаем ВСЕ запросы одновременно через gather
            t_wall_start = time.perf_counter()
            batch = [fire() for _ in range(n)]
            for ok, elapsed in await asyncio.gather(*batch):
                stats.total += 1
                if ok:
                    stats.ok += 1
                    stats.times.append(elapsed)
                else:
                    stats.errors += 1
            t_wall = (time.perf_counter() - t_wall_start) * 1000

            results[label] = stats
            print(
                f"{stats.ok}/{stats.total} OK, "
                f"avg={stats.avg:.1f}ms, wall={t_wall:.0f}ms, "
                f"rps={n / (t_wall / 1000):.0f}"
            )

    return results


# ---------------------------------------------------------------------------
# «Стрельба» по Flask (синхронно через треди)
# ---------------------------------------------------------------------------
async def shoot_flask(n: int, concurrency: int) -> dict[str, Stats]:
    """N запросов к Flask через ThreadPoolExecutor.

    Flask sync + threads: каждый запрос выполняется в отдельном треде.
    Если 200 запросов, то при max_workers=50 первые 50 ждут 50ms,
    затем следующие 50 и т.д. Общее wall-clock время ≈ n/concurrency × sleep.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from flask import Response

    client = make_flask_client()
    results: dict[str, Stats] = {}

    for label, ep in ENDPOINTS.items():
        print(f"  flask:   {label} ...", end=" ", flush=True)
        stats = Stats()

        def fire() -> tuple[bool, float]:
            try:
                t0 = time.perf_counter()
                if ep["method"] == "GET":
                    r: Response = client.get(ep["path"])
                else:
                    r: Response = client.post(ep["path"], json=ep.get("body"))
                elapsed = (time.perf_counter() - t0) * 1000
                return r.status_code < 500, elapsed
            except Exception:
                return False, 0.0

        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            t_wall_start = time.perf_counter()
            futures = [pool.submit(fire) for _ in range(n)]
            for f in as_completed(futures):
                ok, elapsed = f.result()
                stats.total += 1
                if ok:
                    stats.ok += 1
                    stats.times.append(elapsed)
                else:
                    stats.errors += 1
            t_wall = (time.perf_counter() - t_wall_start) * 1000

        results[label] = stats
        print(
            f"{stats.ok}/{stats.total} OK, "
            f"avg={stats.avg:.1f}ms, wall={t_wall:.0f}ms, "
            f"rps={n / (t_wall / 1000):.0f}"
        )

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main():
    parser = argparse.ArgumentParser(
        description="Нагрузочная пушка для сравнения фреймворков"
    )
    parser.add_argument(
        "--app",
        choices=["fastapi", "flask"],
        default=None,
        help="Тестировать только указанный фреймворк",
    )
    parser.add_argument(
        "-n",
        type=int,
        default=500,
        help="Количество запросов на эндпоинт (default: 200)",
    )
    parser.add_argument(
        "-c", "--concurrency", type=int, default=50, help="Concurrency (default: 50)"
    )
    args = parser.parse_args()

    n = args.n
    concurrency = args.concurrency

    print("=" * 65)
    print("  Нагрузочное тестирование: сравнение фреймворков")
    print(f"  Запросов: {n}  |  Concurrency: {concurrency}")
    print()

    all_results: dict[str, dict[str, Stats]] = {}

    shooters: dict[str, callable] = {
        "fastapi": shoot_fastapi,
        "flask": shoot_flask,
    }

    for app_name in list(shooters.keys()):
        print(f"[{app_name}] Стреляю...")
        shooter = shooters.get(app_name)
        if shooter is None:
            continue
        results = await shooter(n, concurrency)
        all_results[app_name] = results
        print()


if __name__ == "__main__":
    asyncio.run(main())
