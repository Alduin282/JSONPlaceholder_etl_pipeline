import os
import pytest
from src.db import get_connection
from src import config


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test.db"
    original_db = config.DB_PATH
    config.DB_PATH = str(db_file)

    yield db_file

    config.DB_PATH = original_db
    if db_file.exists():
        os.remove(db_file)


def test__connection__opened__foreign_keys_enabled(test_db):
    # Act
    with get_connection() as conn:
        fk_status = conn.execute("PRAGMA foreign_keys").fetchone()[0]

    # Assert
    assert fk_status == 1


def test__connection__opened__wal_mode_enabled(test_db):
    # Act
    with get_connection() as conn:
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]

    # Assert
    assert journal_mode.lower() == "wal"


def test__transaction__exception_raised__rolled_back(test_db):
    # Arrange
    with get_connection() as conn:
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")

    # Act
    try:
        with get_connection() as conn:
            conn.execute("INSERT INTO test VALUES (1)")
            raise ValueError("Failure")
    except ValueError:
        pass

    # Assert
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM test").fetchone()[0]
        assert count == 0


def test__transaction__success__committed(test_db):
    # Arrange
    with get_connection() as conn:
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")

    # Act
    with get_connection() as conn:
        conn.execute("INSERT INTO test VALUES (1)")

    # Assert
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM test").fetchone()[0]
        assert count == 1
