import logging
from typing import List, Dict, Any

from sqlmodel import Session, SQLModel, inspect
from sqlalchemy.dialects.sqlite import insert

logger = logging.getLogger(__name__)


class Repository:
    def create_tables(self, engine) -> None:
        SQLModel.metadata.create_all(engine)
        logger.info("Схема БД синхронизирована")

    def upsert_many(self, session: Session, model_class: Any, data: List[Dict[str, Any]]) -> int:
        if not data:
            return 0

        # Базовый стейтмент вставки
        stmt = insert(model_class).values(data)

        # Получаем информацию о модели через интроспекцию
        mapper = inspect(model_class)
        primary_keys = [key.name for key in mapper.primary_key]

        # Формируем словарь полей для обновления при конфликте (все кроме PK)
        update_cols = {col.name: stmt.excluded[col.name] for col in mapper.columns if col.name not in primary_keys}

        # Добавляем логику ON CONFLICT для SQLite
        upsert_stmt = stmt.on_conflict_do_update(index_elements=primary_keys, set_=update_cols)

        session.execute(upsert_stmt)
        logger.debug("UPSERT %s: %d записей", model_class.__name__, len(data))
        return len(data)
