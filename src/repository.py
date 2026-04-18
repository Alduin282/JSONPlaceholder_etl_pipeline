import logging
from typing import List, Dict, Any, Protocol
from abc import abstractmethod

from sqlmodel import Session, SQLModel, inspect
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

logger = logging.getLogger(__name__)


class BaseRepository(Protocol):
    @abstractmethod
    def create_tables(self, engine) -> None: ...

    @abstractmethod
    def upsert_many(
        self, session: Session, model_class: Any, records: List[Dict[str, Any]]
    ) -> int: ...


class SQLiteRepository:
    def create_tables(self, engine) -> None:
        SQLModel.metadata.create_all(engine)
        logger.info("Схема БД синхронизирована (SQLite)")

    def upsert_many(
        self, session: Session, model_class: Any, records: List[Dict[str, Any]]
    ) -> int:
        if not records:
            return 0

        statement = sqlite_insert(model_class).values(records)

        mapper = inspect(model_class)
        primary_keys = [key.name for key in mapper.primary_key]

        update_columns = {
            column.name: statement.excluded[column.name]
            for column in mapper.columns
            if column.name not in primary_keys
        }

        upsert_statement = statement.on_conflict_do_update(
            index_elements=primary_keys, set_=update_columns
        )

        session.exec(upsert_statement)
        logger.debug(
            "UPSERT %s: %d записей (SQLite)", model_class.__name__, len(records)
        )
        return len(records)
