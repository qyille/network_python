# demo_gun — Нагрузочная пушка

Сравнивает производительность **FastAPI** (async) и **Flask** (sync)
на одинаковых эндпоинтах с симуляцией I/O.

## Установка

```bash
cd examples/demo_gun
pip install -r requirements.txt
```

## Запуск

```bash
# Протестировать всё (FastAPI + Flask), 200 запросов, concurrency=20
python gun.py

# Только один фреймворк
python gun.py --app fastapi
python gun.py --app flask

# Настроить нагрузку
python gun.py -n 500 -c 50
```
