# Лекция 3. gRPC в Python

## Установка зависимостей

```bash
# Создать виртуальное окружение (если ещё не создано)
python3 -m venv .venv

# Активировать
source .venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

## Генерация pb2-файлов

Примеры используют protobuf — перед запуском нужно сгенерировать код из `.proto`:

```bash
# Установить grpcio-tools (входит в requirements.txt)
# Сгенерировать все примеры:
bash generate_all.sh
```

Скрипт нужно запускать из папки `03_lecture/`.

## Структура

```
03_lecture/
├── README.md
├── requirements.txt
├── generate_all.sh           # генерация всех pb2-файлов
│
├── examples/
│   ├── 01_hello_grpc/        # Минимальный gRPC: Greeter
│   ├── 02_streaming/         # 4 типа gRPC-стримов
│   ├── 03_grpc_vs_rest/      # Сравнение gRPC и REST
│   └── 04_errors_interceptors/  # Обработка ошибок + интерцепторы
```
