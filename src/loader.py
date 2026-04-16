"""
loader.py — Оркестратор ETL-процесса.

Соединяет ApiClient и Repository.
Отвечает за:
- Последовательность загрузки (users -> posts -> comments)
- Валидацию данных через Pydantic-модели
- Логирование процесса и обработку ошибок на уровне ресурсов

НЕ знает ничего об HTTP-заголовках или SQL-диалектах.
"""

import logging
from typing import Any, Type, TypeVar

from pydantic import BaseModel, ValidationError as PydanticValidationError

from src.api_client import ApiClient
from src.db import get_connection
from src.exceptions import ValidationError
from src.models import Comment, Post, User
from src.repository import Repository

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class Loader:
    """Оркестратор для загрузки данных из JSONPlaceholder в SQLite."""

    def __init__(self, api_client: ApiClient, repository: Repository) -> None:
        """
        Инициализировать загрузчик.

        :param api_client: Клиент для получения данных из API.
        :param repository: Репозиторий для сохранения данных в БД.
        """
        self._api = api_client
        self._repo = repository

    def run(self) -> None:
        """
        Запустить полный ETL-цикл.

        Порядок важен из-за Foreign Key: сначала пользователи, потом посты,
        потом комментарии. Каждый ресурс загружается независимо.
        """
        logger.info("=== ETL-процесс начат ===")
        self._ensure_schema()
        self._load_users()
        self._load_posts()
        self._load_comments()
        logger.info("=== ETL-процесс завершён ===")

    def _ensure_schema(self) -> None:
        """Создать таблицы, если их нет (отдельная транзакция)."""
        with get_connection() as conn:
            self._repo.create_tables(conn)

    def _load_users(self) -> None:
        """
        Загрузить, провалидировать и сохранить пользователей.

        Пользователи сохраняются атомарно: основная запись + адрес + компания
        в рамках одной транзакции.
        """
        logger.info("--- Загрузка users ---")
        raw: list[dict[str, Any]] = self._api.get_users()
        users = self._validate_many(raw, User, resource="users")

        if not users:
            logger.warning("Нет валидных users для сохранения, пропускаем")
            return

        with get_connection() as conn:
            # Сохраняем все части пользователя атомарно (в одной транзакции)
            count = self._repo.upsert_users(conn, users)
            self._repo.upsert_user_addresses(conn, users)
            self._repo.upsert_user_companies(conn, users)

        logger.info("users (и доп. данные) сохранено: %d", count)

    def _load_posts(self) -> None:
        """Загрузить, провалидировать и сохранить посты."""
        logger.info("--- Загрузка posts ---")
        raw: list[dict[str, Any]] = self._api.get_posts()
        posts = self._validate_many(raw, Post, resource="posts")

        if not posts:
            logger.warning("Нет валидных posts для сохранения, пропускаем")
            return

        with get_connection() as conn:
            count = self._repo.upsert_posts(conn, posts)
        logger.info("posts сохранено: %d", count)

    def _load_comments(self) -> None:
        """Загрузить, провалидировать и сохранить комментарии."""
        logger.info("--- Загрузка comments ---")
        raw: list[dict[str, Any]] = self._api.get_comments()
        comments = self._validate_many(raw, Comment, resource="comments")

        if not comments:
            logger.warning("Нет валидных comments для сохранения, пропускаем")
            return

        with get_connection() as conn:
            count = self._repo.upsert_comments(conn, comments)
        logger.info("comments сохранено: %d", count)

    @staticmethod
    def _validate_many(
        raw_items: list[dict[str, Any]],
        model: Type[T],
        resource: str,
    ) -> list[T]:
        """
        Провалидировать список сырых словарей через Pydantic-модель.

        Если одна запись битая — логируем WARNING и идем дальше.
        Если НИ ОДНА запись в батче не валидна — выбрасываем ValidationError.
        """
        valid: list[T] = []
        for item in raw_items:
            try:
                valid.append(model(**item))
            except PydanticValidationError as exc:
                logger.warning(
                    "Запись %s (id=%s) не прошла валидацию: %s",
                    resource,
                    item.get("id"),
                    exc.errors()[0]["msg"],
                )

        if not valid and raw_items:
            raise ValidationError(f"Все {len(raw_items)} записей {resource} не прошли валидацию")

        logger.debug("%s: успешно провалидировано %d записей", resource, len(valid))
        return valid
