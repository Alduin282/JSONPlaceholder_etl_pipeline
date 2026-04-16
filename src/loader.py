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
    def __init__(self, api_client: ApiClient, repository: Repository) -> None:
        self._api = api_client
        self._repo = repository

    def run(self) -> None:
        logger.info("=== ETL-процесс начат ===")
        self._ensure_schema()
        self._load_users()
        self._load_posts()
        self._load_comments()
        logger.info("=== ETL-процесс завершён ===")

    def _ensure_schema(self) -> None:
        with get_connection() as conn:
            self._repo.create_tables(conn)

    def _load_users(self) -> None:
        logger.info("--- Загрузка users ---")
        raw: list[dict[str, Any]] = self._api.get_users()
        users = self._validate_many(raw, User, resource="users")

        if not users:
            logger.warning("Нет валидных users для сохранения, пропускаем")
            return

        with get_connection() as conn:
            count = self._repo.upsert_users(conn, users)
            self._repo.upsert_user_addresses(conn, users)
            self._repo.upsert_user_companies(conn, users)

        logger.info("users (и доп. данные) сохранено: %d", count)

    def _load_posts(self) -> None:
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
