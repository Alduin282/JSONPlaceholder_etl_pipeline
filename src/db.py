import logging
from contextlib import contextmanager
from typing import Generator

import sqlalchemy
from sqlmodel import Session, create_engine
from src import config
from src.exceptions import DatabaseError

logger = logging.getLogger(__name__)


def get_engine_args(url: str) -> dict:
    args = {"echo": config.SQL_ECHO}
    if url.startswith("sqlite"):
        args["connect_args"] = {"check_same_thread": False}
    return args


engine = create_engine(config.DATABASE_URL, **get_engine_args(config.DATABASE_URL))


@sqlalchemy.event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if config.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
        logger.debug("SQLite PRAGMAs applied (FK=ON, WAL)")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        try:
            yield session
        except sqlalchemy.exc.SQLAlchemyError as exc:
            logger.error("Ошибка уровня базы данных: %s", exc)
            raise DatabaseError(f"Ошибка БД: {exc}") from exc
        except Exception:
            logger.error("Непредвиденная системная ошибка в сессии")
            raise
