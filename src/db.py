"""
db.py — ConnectionHelper: контекстный менеджер SQLite-подключения.

Отвечает исключительно за:
- Открытие / закрытие соединения
- Включение WAL-режима и поддержки FK
- Явное управление транзакциями (commit / rollback)

Ни один другой модуль не вызывает sqlite3.connect() напрямую.
Это дает нам полный контроль над атомарностью операций.
"""

import logging
import sqlite3
from contextlib import contextmanager
from typing import Generator

from src.config import DB_PATH
from src.exceptions import DatabaseError

logger = logging.getLogger(__name__)


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Контекстный менеджер для SQLite-подключения с явным управлением транзакциями.

    Особенности:
    - isolation_level=None -> autocommit ВЫКЛЮЧЕН; мы сами управляем BEGIN/COMMIT.
    - PRAGMA foreign_keys=ON -> FK-ограничения активны.
    - PRAGMA journal_mode=WAL -> меньше блокировок при конкурентном доступе.
    """
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(DB_PATH, isolation_level=None)
        conn.row_factory = sqlite3.Row  # доступ к колонкам по имени

        # Включаем FK и WAL один раз после открытия
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")

        # Начинаем транзакцию вручную. Это гарантирует, что все последующие
        # изменения будут атомарными до вызова COMMIT.
        conn.execute("BEGIN")
        logger.debug("SQLite-соединение открыто: %s", DB_PATH)

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
        # Нереляционные ошибки (например, LogicError) — тоже откатываем транзакцию
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
