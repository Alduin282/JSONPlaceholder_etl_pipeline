# JSONPlaceholder ETL Pipeline

**Версия:** 1.0.0
Сделано в рамках тестового задания для Чиббис (Data Engineer)

Коротко: ETL-скрипт для загрузки данных из JSONPlaceholder (users, posts, comments) в локальную SQLite базу с нормализацией адресов и компаний, валидацией через Pydantic и идемпотентными UPSERT-операциями.

## Что важно

- Нормализованная схема: `users`, `user_addresses`, `user_companies`, `posts`, `comments`.
- Валидация через Pydantic (строго проверяется формат email и обязательные поля).
- Повторные попытки при сетевых ошибках (3 попытки, экспоненциальный бэкофф).
- Идемпотентность: повторный запуск не создаёт дубликатов.

## Схема таблиц (связи)

```
users
├─ user_addresses     (1:1)
├─ user_companies     (1:1)
└─ posts              (1:N)
	└─ comments        (1:N)
```

Кардинальности:
- `1:1` — одна запись пользователя соответствует одной записи в `user_addresses`/`user_companies`;
- `1:N` — у одного пользователя может быть много `posts`, у каждого `post` — много `comments`.

## Быстрый старт (кратко)

1) Установите Python (рекомендуется 3.10+). На Windows скачайте установщик с https://www.python.org/downloads/ и при установке включите "Add Python to PATH".

2) Убедитесь, что `pip` доступен и обновите его:

```powershell
python -m pip install --upgrade pip
```

3) Создайте виртуальное окружение и установите зависимости:

```powershell
python -m venv .venv
.\.venv\Scripts\activate   # Windows
# Или: source .venv/bin/activate  # Linux / macOS
pip install -r requirements.txt
```

4) Запустите ETL:

```powershell
python main.py
```

После выполнения в корне проекта появится файл базы (по умолчанию `jsonplaceholder.db`).

## Конфигурация

Все настройки находятся в `src/config.py`:
- `DB_PATH`: Путь к базе данных (по умолчанию `jsonplaceholder.db`).
- `MAX_RETRIES`: Количество повторных попыток (по умолчанию 2, итого 3 попытки).
- `REQUEST_TIMEOUT`: Таймаут запроса (30 сек для стабильной загрузки `/comments`).

## Тесты

```powershell
pytest
```

## Полезные замечания

- Если база занята: закройте программы, использующие файл `.db`.
- Для детальной отладки включите логирование SQL в `src/config.py`.

