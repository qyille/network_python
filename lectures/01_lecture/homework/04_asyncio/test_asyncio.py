"""Тесты к ДЗ 4: Asyncio."""

import sys
import os
import asyncio
import time
import inspect
import pytest

# Загружаем локальный task.py, а не закешированный из соседнего каталога
sys.path.insert(0, os.path.dirname(__file__))
if "task" in sys.modules:
    del sys.modules["task"]

from task import (
    fetch_one_async,
    fetch_all_async,
    run_task_group,
    fetch_with_timeout,
    cancellable_worker,
    run_with_cancel,
    fetch_as_completed,
    async_process_numbers,
    blocking_compute,
)


# ═══════════════════════════════════════════════════════════
# ЗАДАНИЕ 4.1 — Первая корутина
# ═══════════════════════════════════════════════════════════


class TestFetchOneAsync:
    """Тесты для fetch_one_async()."""

    def test_returns_correct_data(self):
        result = asyncio.run(fetch_one_async("test"))
        assert result == "data:test", f"Ожидали 'data:test', получили {result}"

    def test_is_coroutine(self):
        assert inspect.iscoroutinefunction(fetch_one_async), (
            "fetch_one_async должна быть async def функцией"
        )

    def test_uses_await(self):
        """Проверяем, что функция действительно асинхронная."""
        start = time.perf_counter()
        asyncio.run(fetch_one_async("x"))
        elapsed = time.perf_counter() - start
        assert elapsed < 0.1, (
            f"Слишком медленно: {elapsed:.3f}с. "
            f"Убедитесь, что используете await asyncio.sleep(), "
            f"а не time.sleep()"
        )


# ═══════════════════════════════════════════════════════════
# ЗАДАНИЕ 4.2 — Параллельный запуск
# ═══════════════════════════════════════════════════════════


class TestFetchAllAsync:
    """Тесты для fetch_all_async()."""

    def test_returns_correct_data(self):
        result = asyncio.run(fetch_all_async(["a", "b"]))
        assert result == ["data:a", "data:b"]

    def test_faster_than_sequential(self):
        urls = [str(i) for i in range(10)]
        start = time.perf_counter()
        _ = asyncio.run(fetch_all_async(urls))
        elapsed = time.perf_counter() - start
        assert elapsed < 0.15, (
            f"Слишком медленно: {elapsed:.3f}с. "
            f"Ожидалось ~0.05с при параллельном запуске 10 URL. "
            f"Возможно, корутины запускаются последовательно, "
            f"а не через asyncio.gather()"
        )

    def test_empty_input(self):
        result = asyncio.run(fetch_all_async([]))
        assert result == []

    def test_single_url(self):
        result = asyncio.run(fetch_all_async(["only"]))
        assert result == ["data:only"]

    def test_preserves_order(self):
        urls = [str(i) for i in range(20)]
        result = asyncio.run(fetch_all_async(urls))
        expected = [f"data:{u}" for u in urls]
        assert result == expected, (
            "Порядок должен сохраняться. "
            "Проверьте, что asyncio.gather() сохраняет порядок"
        )


# ═══════════════════════════════════════════════════════════
# ЗАДАНИЕ 4.3 — Групповой запуск (TaskGroup)
# ═══════════════════════════════════════════════════════════


class TestRunTaskGroup:
    """Тесты для run_task_group()."""

    def test_all_success(self):
        result = asyncio.run(run_task_group(["a", "b", "c"]))
        expected = {"a": "data:a", "b": "data:b", "c": "data:c"}
        assert result == expected, (
            f"Все должны быть успешны: ожидали {expected}, получили {result}"
        )

    def test_some_fail(self):
        """Плохие имена возвращают None."""
        result = asyncio.run(run_task_group(["good", "bad", "nice", "bad2"]))
        assert result["good"] == "data:good", (
            f"good должен быть успешен, получили {result['good']}"
        )
        assert result["bad"] is None, f"bad должен быть None, получили {result['bad']}"
        assert result["nice"] == "data:nice", f"nice должен быть успешен"
        assert result["bad2"] is None, f"bad2 должен быть None"

    def test_all_fail(self):
        """Все задачи упали — пустой словарь."""
        result = asyncio.run(run_task_group(["bad1", "bad2"]))
        assert result == {}, f"Ожидали пустой словарь, получили {result}"

    def test_empty(self):
        result = asyncio.run(run_task_group([]))
        assert result == {}

    def test_uses_task_group(self):
        """Проверяем, что используется TaskGroup (не gather)."""
        names = ["a", "b", "c"]
        result = asyncio.run(run_task_group(names))
        assert all(v is not None for v in result.values())


# ═══════════════════════════════════════════════════════════
# ЗАДАНИЕ 4.4 — Таймауты
# ═══════════════════════════════════════════════════════════


class TestFetchWithTimeout:
    """Тесты для fetch_with_timeout()."""

    def test_success_within_timeout(self):
        """Успеваем до таймаута."""
        result = asyncio.run(fetch_with_timeout("ok", delay=0.05, timeout=2.0))
        assert result == "data:ok", f"Ожидали 'data:ok', получили {result}"

    def test_timeout_exceeded(self):
        """Не уложились — TimeoutError."""
        with pytest.raises(TimeoutError):
            asyncio.run(fetch_with_timeout("slow", delay=5.0, timeout=0.1))

    def test_timeout_is_fast(self):
        """Таймаут срабатывает быстро, без ожидания всей задержки."""
        start = time.perf_counter()
        try:
            asyncio.run(fetch_with_timeout("slow", delay=10.0, timeout=0.05))
        except TimeoutError:
            elapsed = time.perf_counter() - start
            assert elapsed < 1.0, (
                f"Таймаут должен сработать быстро, но прошло {elapsed:.3f}с"
            )
        else:
            pytest.fail("Ожидали TimeoutError, но исключение не было выброшено")

    def test_zero_timeout(self):
        """Таймаут 0 — всегда TimeoutError."""
        with pytest.raises(TimeoutError):
            asyncio.run(fetch_with_timeout("nope", delay=0.1, timeout=0))


# ═══════════════════════════════════════════════════════════
# ЗАДАНИЕ 4.5 — Отмена задач
# ═══════════════════════════════════════════════════════════


class TestCancellableWorker:
    """Тесты для cancellable_worker()."""

    def test_completes_normally(self):
        """Без отмены задача завершается."""
        result = asyncio.run(cancellable_worker("test", 3))
        expected = "test: готов после 3 шагов"
        assert result == expected, f"Ожидали '{expected}', получили '{result}'"

    def test_raises_cancelled_error(self):
        """При отмене задача пробрасывает CancelledError."""

        async def run():
            task = asyncio.create_task(cancellable_worker("to-cancel", 10))
            await asyncio.sleep(0.15)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        asyncio.run(run())


class TestRunWithCancel:
    """Тесты для run_with_cancel()."""

    def test_completes_before_cancel(self):
        """Успевает до отмены."""
        result = asyncio.run(run_with_cancel("fast", steps=1, cancel_after=5.0))
        assert result == "fast: готов после 1 шагов", (
            f"Должна успеть завершиться, получили {result}"
        )

    def test_cancelled_returns_none(self):
        """Отменяем вовремя — возвращает None."""
        result = asyncio.run(run_with_cancel("slow", steps=20, cancel_after=0.1))
        assert result is None, (
            f"Отменённая задача должна вернуть None, получили {result}"
        )

    def test_cancel_is_clean(self):
        """После отмены нет зависших задач."""

        async def run():
            result = await run_with_cancel("clean", steps=50, cancel_after=0.05)
            # После возврата не должно быть активных задач (кроме текущей)
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            assert len(tasks) == 0, f"Остались незавершённые задачи: {tasks}"
            return result

        result = asyncio.run(run())
        assert result is None


# ═══════════════════════════════════════════════════════════
# ЗАДАНИЕ 4.6 — Асинхронный as_completed
# ═══════════════════════════════════════════════════════════


class TestFetchAsCompleted:
    """Тесты для fetch_as_completed()."""

    def test_returns_all_results(self):
        """Все результаты возвращены."""
        tasks = [("A", 0.05), ("B", 0.05), ("C", 0.05)]
        result = asyncio.run(fetch_as_completed(tasks))
        assert len(result) == 3, f"Ожидали 3 результата, получили {len(result)}"

    def test_fastest_comes_first(self):
        """Самый быстрый результат должен быть первым (as_completed)."""
        tasks = [("slow", 0.3), ("fast", 0.05), ("medium", 0.15)]
        result = asyncio.run(fetch_as_completed(tasks))

        # "fast" должен быть среди первых двух (с учётом случайностей планировщика)
        first_two = result[:2]
        assert any("fast" in r for r in first_two), (
            f"Быстрый запрос должен прийти раньше медленного.\n"
            f"Порядок: {result}. "
            f"Убедитесь, что используете asyncio.as_completed(), "
            f"а не собираете все результаты через gather"
        )

    def test_empty(self):
        """Пустой список."""
        result = asyncio.run(fetch_as_completed([]))
        assert result == []

    def test_single(self):
        """Один элемент."""
        result = asyncio.run(fetch_as_completed([("only", 0.05)]))
        assert result == ["only: готов за 0.05с"]

    def test_order_is_not_original(self):
        """Порядок результатов отличается от порядка запуска (разные задержки)."""
        tasks = [("long", 0.5), ("quick", 0.05), ("instant", 0.01)]
        result = asyncio.run(fetch_as_completed(tasks))
        # Последний — самый медленный
        assert "long" in result[-1], (
            f"Самый медленный (long) должен быть последним.\nПорядок: {result}"
        )


# ═══════════════════════════════════════════════════════════
# ЗАДАНИЕ 4.7 — Смешивание sync и async
# ═══════════════════════════════════════════════════════════


class TestAsyncProcessNumbers:
    """Тесты для async_process_numbers()."""

    def test_returns_correct_values(self):
        numbers = [5, 10, 15]
        result = asyncio.run(async_process_numbers(numbers, max_workers=2))
        expected = [blocking_compute(n) for n in numbers]
        assert result == expected, f"Ожидали {expected}, получили {result}"

    def test_does_not_block_event_loop(self):
        """Проверяем, что event loop не блокируется."""

        async def run_test():
            coro = async_process_numbers([10, 20, 30], max_workers=2)
            return await asyncio.wait_for(coro, timeout=2.0)

        result = asyncio.run(run_test())
        assert len(result) == 3

    def test_concurrent_faster(self):
        """Больше workers — быстрее (в ThreadPoolExecutor)."""
        numbers = list(range(200, 300))

        start = time.perf_counter()
        result_1 = asyncio.run(async_process_numbers(numbers, max_workers=1))
        time_1 = time.perf_counter() - start

        start = time.perf_counter()
        result_4 = asyncio.run(async_process_numbers(numbers, max_workers=4))
        time_4 = time.perf_counter() - start

        assert result_1 == result_4, (
            "Результаты должны совпадать при разном max_workers"
        )
        assert time_4 < time_1 * 0.7, (
            f"max_workers=4 должен быть быстрее max_workers=1:\n"
            f"  workers=1: {time_1:.3f}s\n"
            f"  workers=4: {time_4:.3f}s\n"
        )

    def test_empty(self):
        result = asyncio.run(async_process_numbers([], max_workers=2))
        assert result == []
