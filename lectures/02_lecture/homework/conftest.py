"""Общие фикстуры и настройки pytest для домашних заданий."""

import pytest


def pytest_configure(config):
    """Регистрация кастомных маркеров."""
    config.addinivalue_line(
        "markers",
        "slow: медленные тесты. Запускать отдельно: pytest -m slow",
    )


def pytest_report_header(config):
    return [
        "Домашние задания — Лекция 2: REST API, HTTP, FastAPI",
        "Ожидания: все тесты должны быть зелёными ✅",
    ]
