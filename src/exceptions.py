"""
exceptions.py — Иерархия исключений приложения.

Централизованная иерархия позволяет:
- Ловить всё через AppError в точке входа
- Ловить конкретный тип там, где нужна специфичная реакция
"""


class AppError(Exception):
    """
    Базовый класс для всех ошибок приложения.

    Оставляем его пустым — это стандартная практика создания "маркера" исключений.
    Позволяет ловить все ошибки нашего скрипта через `except AppError`,
    отделяя их от системных ошибок (типа ValueError или KeyError).
    """


class ApiError(AppError):
    """Базовый класс ошибок API-клиента."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class DataNotFoundError(ApiError):
    """HTTP 404 — ресурс не найден. Retry не нужен."""


class ApiClientError(ApiError):
    """HTTP 4xx (кроме 404) — ошибка на стороне клиента. Retry не нужен."""


class ApiServerError(ApiError):
    """HTTP 5xx / timeout / connection — ошибка сервера. Retry исчерпан."""


class ValidationError(AppError):
    """Данные не прошли валидацию Pydantic-схемой."""


class DatabaseError(AppError):
    """Ошибка при работе с SQLite."""
