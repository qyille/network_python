#!/usr/bin/env python3
"""
03_multiprocessing/02_cpu_bound.py — CPU-bound задача: сравнение threading vs multiprocessing.

Считаем простые числа — задача, где GIL мешает threading,
а multiprocessing даёт реальный параллелизм на всех ядрах.

Запуск:
    python lectures/01_lecture/examples_new/03_multiprocessing/02_cpu_bound.py
"""

import time
import math
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor


def count_primes(limit: int) -> int:
    """Количество простых чисел от 2 до limit (CPU-bound)."""
    count = 0
    for n in range(2, limit + 1):
        if all(n % i != 0 for i in range(2, int(math.sqrt(n)) + 1)):
            count += 1
    return count


def main() -> None:
    n_workers = mp.cpu_count()
    limit = 300_000
    print("03_multiprocessing/02_cpu_bound: CPU-bound (простые числа)")
    print("=" * 55)
    print(f"   Ядер CPU: {n_workers}, предел: {limit}")
    print()

    # Последовательно
    start = time.perf_counter()
    for _ in range(n_workers):
        count_primes(limit)
    sync_time = time.perf_counter() - start
    print(f"🐢 Sync (последовательно):    {sync_time:.2f}s")

    # Threading
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        pool.map(count_primes, [limit] * n_workers)
    thread_time = time.perf_counter() - start
    print(
        f"🧵 Threading (GIL мешает):    {thread_time:.2f}s — {sync_time / thread_time:.1f}x"
    )

    # Multiprocessing
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        pool.map(count_primes, [limit] * n_workers)
    proc_time = time.perf_counter() - start
    print(
        f"⚙️  Multiprocessing (обход GIL): {proc_time:.2f}s — {sync_time / proc_time:.1f}x"
    )

    print()
    print("📌 Вывод:")
    print("   Threading: GIL не отпускается → хуже sync")
    print("   Multiprocessing: настоящий параллелизм → ускорение ~Nx")


if __name__ == "__main__":
    main()
