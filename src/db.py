import logging
import sqlite3
from contextlib import contextmanager
from typing import Generator

from src import config
from src.exceptions import DatabaseError

logger = logging.getLogger(__name__)


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(config.DB_PATH, isolation_level=None)
        conn.row_factory = sqlite3.Row

        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")

        # Начинаем транзакцию вручную. Это гарантирует, что все последующие
        # изменения будут атомарными до вызова COMMIT.
        conn.execute("BEGIN")
        logger.debug("SQLite-соединение открыто: %s", config.DB_PATH)

        yield conn

        conn.execute("COMMIT")
        logger.debug("Транзакция зафиксирована (COMMIT)")

    except sqlite3.Error as exc:
        if conn:
            try:
                conn.execute("ROLLBACK")
                logger.warning("Транзакция откатана (ROLLBACK) из-за ошибки SQLite: %s", exc)
            except sqlite3.Error as rollback_exc:
                logger.error("Критическая ошибка: не удалось выполнить ROLLBACK: %s", rollback_exc)
        raise DatabaseError(f"Ошибка SQLite: {exc}") from exc

    except Exception as exc:
        if conn:
            try:
                conn.execute("ROLLBACK")
                logger.warning("Транзакция откатана (ROLLBACK) из-за исключения: %s", exc)
            except sqlite3.Error as rollback_exc:
                logger.error("Критическая ошибка: не удалось выполнить ROLLBACK: %s", rollback_exc)
        raise

    finally:
        if conn:
            conn.close()
            logger.debug("SQLite-соединение закрыто")
