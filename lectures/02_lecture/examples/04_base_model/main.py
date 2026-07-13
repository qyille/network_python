from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional, Union
from datetime import datetime, timezone


app = FastAPI(debug=True)


# -------------------------------------------------------------------
# Базовые возможности BaseModel
# -------------------------------------------------------------------


class Item(BaseModel):
    """Базовая модель — поля с разными типами."""

    name: str
    price: float
    is_offer: bool = False
    tags: list[str] = []
    description: Optional[str] = None


@app.post("/items")
async def create_item(item: Item):
    """Создать товар. FastAPI сам валидирует входящий JSON по Item."""
    return {
        "item": item.model_dump(),
        "price_with_tax": item.price * 1.13,
    }


@app.get("/items/example")
async def item_example():
    """Показать пример JSON Schema, которую генерирует FastAPI."""
    return Item.model_json_schema()


# -------------------------------------------------------------------
# Field — расширенная валидация полей
# -------------------------------------------------------------------


class Product(BaseModel):
    """Модель с валидацией через Field."""

    name: str = Field(min_length=3, max_length=50, examples=["Ноутбук"])
    price: float = Field(gt=0, le=1_000_000, examples=[99_990.0])
    quantity: int = Field(ge=0, default=0, examples=[10])
    code: str = Field(pattern=r"^[A-Z]{2}-\d{4}$", examples=["PR-0001"])


@app.post("/products")
async def create_product(product: Product):
    """Создать товар с расширенной валидацией."""
    return {"product": product.model_dump()}


# -------------------------------------------------------------------
# Union и составные типы
# -------------------------------------------------------------------


class Cat(BaseModel):
    pet_type: str = "cat"
    meow_volume: int = Field(ge=0, le=100)


class Dog(BaseModel):
    pet_type: str = "dog"
    bark_volume: int = Field(ge=0, le=100)


class User(BaseModel):
    name: str
    pet: Optional[Union[Cat, Dog]] = None  # кошка ИЛИ собака, может не быть


@app.post("/users")
async def create_user(user: User):
    """Пользователь с питомцем (Cat | Dog). FastAPI сам разберёт union."""
    return user.model_dump()


# -------------------------------------------------------------------
# Вложенные модели (Nested Models)
# -------------------------------------------------------------------


class Address(BaseModel):
    city: str
    street: str
    building: str


class Order(BaseModel):
    id: int
    customer: str
    items: list[Item]
    address: Address
    total: Optional[float] = None


ORDERS: list[Order] = []


@app.post("/orders")
async def create_order(order: Order):
    """Заказ со вложенными Address и списком Item."""
    total = sum(item.price for item in order.items)
    order.total = round(total, 2)
    ORDERS.append(order)
    return {"order_id": order.id, "total": order.total}


# -------------------------------------------------------------------
# model_dump() vs model_dump_json()
# -------------------------------------------------------------------


class Article(BaseModel):
    title: str
    content: str
    published: bool
    rating: float


@app.get("/articles/dump-demo")
def dump_demo():
    """Разница между dict и JSON-строкой."""
    article = Article(
        title="FastAPI",
        content="Полезный фреймворк",
        published=True,
        rating=4.8,
    )
    return {
        "as_dict": article.model_dump(),
        "as_json": article.model_dump_json(),
    }


# -------------------------------------------------------------------
# Значения по умолчанию через default_factory
# -------------------------------------------------------------------


class LogEntry(BaseModel):
    message: str
    level: str = "info"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@app.post("/logs")
async def create_log(log: LogEntry):
    """Каждый раз — новое timestamp (default_factory)."""
    return log.model_dump()
