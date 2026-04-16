class AppError(Exception):
    """
    Базовый класс для всех ошибок приложения.
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
