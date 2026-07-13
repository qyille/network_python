"""Автотесты для demo_gun — проверяем, что пушка не падает."""

import asyncio

from gun import shoot_fastapi, shoot_flask


def test_fastapi_shoot():
    """Проверяем, что FastAPI-пушка отрабатывает без ошибок."""
    results = asyncio.run(shoot_fastapi(n=5, concurrency=3))
    for label, stats in results.items():
        assert stats.ok == 5, f"{label}: {stats.ok}/{stats.total} OK"


def test_flask_shoot():
    """Проверяем, что Flask-пушка отрабатывает без ошибок."""
    results = asyncio.run(shoot_flask(n=5, concurrency=3))
    for label, stats in results.items():
        assert stats.ok == 5, f"{label}: {stats.ok}/{stats.total} OK"
