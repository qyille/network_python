import pytest
from starlette.testclient import TestClient

from demo_tests.main import app

client = TestClient(app)


# -------------------------------------------------------------------
# Базовые тесты
# -------------------------------------------------------------------


def test_root():
    """GET / — корневой эндпоинт."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == '"Hello!"'


def test_get_posts_list():
    """GET /posts — список всех постов."""
    response = client.get("/posts")
    assert response.status_code == 200
    data = response.json()
    assert "posts" in data
    assert len(data["posts"]) >= 2


def test_get_post_by_id():
    """GET /posts/0 — получение поста по id."""
    response = client.get("/posts/0")
    assert response.status_code == 200
    assert response.json() == {"post": {"text": "Hello world!"}}


# -------------------------------------------------------------------
# Тесты HTTP-статусов и ошибок
# -------------------------------------------------------------------


def test_post_42_forbidden():
    """GET /posts/42 — хост завёл специальную обработку для 42."""
    response = client.get("/posts/42")
    assert response.status_code == 418
    assert response.json() == {"detail": "42 is forbidden."}


def test_post_not_found():
    """GET /posts/999 — несуществующий индекс → IndexError → 404."""
    response = client.get("/posts/999")
    assert response.status_code == 404
    assert response.json() == {"message": "No such element"}


def test_post_negative_id():
    """GET /posts/-1 — отрицательный индекс = последний элемент (не ошибка)."""
    response = client.get("/posts/-1")
    assert response.status_code == 200


def test_not_found():
    """GET /nonexistent — несуществующий маршрут → 404."""
    response = client.get("/nonexistent")
    assert response.status_code == 404


# -------------------------------------------------------------------
# POST — создание
# -------------------------------------------------------------------


def test_create_post():
    """POST /posts — успешное создание."""
    response = client.post("/posts", json={"text": "Новый пост"})
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Post added"

    get_response = client.get("/posts")
    posts = get_response.json()["posts"]
    assert any(p["text"] == "Новый пост" for p in posts)


def test_create_post_empty_text():
    """POST /posts — пустой текст (валидно, т.к. str без ограничений)."""
    response = client.post("/posts", json={"text": ""})
    assert response.status_code == 201


# -------------------------------------------------------------------
# POST — невалидные данные
# -------------------------------------------------------------------


def test_create_post_missing_field():
    """POST /posts — без обязательного поля text → 422."""
    response = client.post("/posts", json={})
    assert response.status_code == 422


def test_create_post_wrong_type():
    """POST /posts — text не строка → 422."""
    response = client.post("/posts", json={"text": 123})
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("text" in str(e) for e in errors)


def test_create_post_extra_field():
    """POST /posts — лишнее поле игнорируется (Pydantic по умолчанию)."""
    response = client.post("/posts", json={"text": "ok", "extra": "ignored"})
    assert response.status_code == 201


# -------------------------------------------------------------------
# GET /posts/mine
# -------------------------------------------------------------------


def test_get_posts_mine():
    """GET /posts/mine — маршрут /mine (важен порядок: до /{post_id})."""
    response = client.get("/posts/mine")
    assert response.status_code == 200
    assert response.json() == {"posts": ["User posts"]}


# -------------------------------------------------------------------
# GET /posts/find?query=...
# -------------------------------------------------------------------


def test_find_posts():
    """GET /posts/find — поиск с query-параметром."""
    response = client.get("/posts/find", params={"query": "hello"})
    assert response.status_code == 200
    assert response.json() == {"query": "hello"}


def test_find_posts_empty_query():
    """GET /posts/find — пустой query."""
    response = client.get("/posts/find", params={"query": ""})
    assert response.status_code == 200


def test_find_posts_no_query():
    """GET /posts/find — без query → 422 (обязательный параметр)."""
    response = client.get("/posts/find")
    assert response.status_code == 422


# -------------------------------------------------------------------
# Content-Type и заголовки
# -------------------------------------------------------------------


def test_content_type_json():
    """Ответы приходят с Content-Type: application/json."""
    response = client.get("/posts/0")
    assert response.headers["content-type"] == "application/json"


def test_content_type_returned():
    """Ответы всегда приходят с Content-Type."""
    response = client.get("/")
    assert "content-type" in response.headers


# -------------------------------------------------------------------
# Параметризованные тесты
# -------------------------------------------------------------------


@pytest.mark.parametrize(
    "post_id, expected_status",
    [
        (0, 200),
        (1, 200),
        (42, 418),
        (999, 404),
    ],
)
def test_multiple_posts_parametrized(post_id, expected_status):
    """Параметризация — один тест на несколько кейсов."""
    response = client.get(f"/posts/{post_id}")
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "payload, expected_status",
    [
        ({"text": "hello"}, 201),
        ({"text": ""}, 201),
        ({}, 422),
        ({"text": 42}, 422),
        ({"text": "x", "extra": "y"}, 201),
    ],
)
def test_create_post_parametrized(payload, expected_status):
    """Параметризация — разные payload на создание поста."""
    response = client.post("/posts", json=payload)
    assert response.status_code == expected_status


# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------


@pytest.fixture
def sample_payload():
    """Фикстура — типовой payload для создания поста."""
    return {"text": "Post from fixture"}


def test_create_post_with_fixture(sample_payload):
    """Использование фикстуры sample_payload."""
    response = client.post("/posts", json=sample_payload)
    assert response.status_code == 201


# -------------------------------------------------------------------
# Маркировка и пропуск тестов
# -------------------------------------------------------------------


@pytest.mark.slow
def test_slow_marker_example():
    """Пример: тест, помеченный как slow (запуск: pytest -m slow)."""
    response = client.get("/posts")
    assert response.status_code == 200


@pytest.mark.skip(reason="Демонстрация пропуска теста")
def test_skipped_example():
    """Этот тест всегда пропускается."""
    assert False


@pytest.mark.skipif(True, reason="Демонстрация условного пропуска")
def test_skipif_example():
    """Пропускается, если условие истинно."""
    assert False
