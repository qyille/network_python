# gRPC vs REST: Сравнение на Bookstore

Один и тот же CRUD-сервис "Книжный магазин" реализован двумя способами:

| Характеристика | REST (FastAPI) | gRPC |
|---|---|---|
| Протокол | HTTP/1.1 | HTTP/2 |
| Формат данных | JSON (текст) | Protobuf (бинарный) |
| Типизация | runtime (Pydantic) | compile-time (.proto) |
| Документация | Swagger/OpenAPI автоматом | .proto-файлы |
| Читаемость | ✅ читаемый JSON | ❌ бинарный, нужен protoc |
| Браузер/curl | ✅ да | ❌ нет |
| Streaming | ❌ сложно (SSE) | ✅ нативно |
| Размер payload | ~3-5x больше | компактный |
| Скорость | медленнее | быстрее |

## Запуск бенчмарка

```bash
# (из корня 03_lecture, с активированным .venv)
python examples/03_grpc_vs_rest/benchmark.py
```

Бенчмарк запускает оба сервера in-process, выполняет CRUD и замеряет время и размер ответов.
