# Лекция 1. Асинхронность и конкурентность в Python

## Установка зависимостей

```bash
# Создать виртуальное окружение (если ещё не создано)
python3 -m venv .venv

# Активировать
source .venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

## Подключение .venv к Jupyter

Чтобы ноутбук `lecture.ipynb` работал в созданном виртуальном окружении,
нужно добавить его как ядро (kernel) в Jupyter:

```bash
# Активировать виртуальное окружение (если ещё не активировано)
source .venv/bin/activate

# Установить ipykernel (входит в зависимости через notebook)
# Зарегистрировать .venv как ядро Jupyter
python -m ipykernel install --user --name=network_python --display-name="Python (network_python)"
```

После этого при открытии `lecture.ipynb` в Jupyter выберите Kernel → Change kernel → **Python (network_python)**.

### Проверка

Откройте ноутбук и выполните первую ячейку с кодом:

```python
import sys
print(sys.executable)
```

Путь должен указывать на `.venv/bin/python`.
