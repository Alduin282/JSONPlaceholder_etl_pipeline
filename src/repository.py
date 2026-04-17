import logging
from typing import List, Dict, Any

from sqlmodel import Session, SQLModel, inspect
from sqlalchemy.dialects.sqlite import insert

logger = logging.getLogger(__name__)


class Repository:
    def create_tables(self, engine) -> None:
        SQLModel.metadata.create_all(engine)
        logger.info("Схема БД синхронизирована")

    def upsert_many(
        self, session: Session, model_class: Any, records: List[Dict[str, Any]]
    ) -> int:
        if not records:
            return 0

        statement = insert(model_class).values(records)

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
        logger.debug("UPSERT %s: %d записей", model_class.__name__, len(records))
        return len(records)
