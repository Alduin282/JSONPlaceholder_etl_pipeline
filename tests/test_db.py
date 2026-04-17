import pytest
from sqlalchemy import text
from src.db import get_session, engine
from src import config


@pytest.fixture
def test_db(tmp_path):
    # Arrange
    db_file = tmp_path / "test.db"
    original_db = config.DB_PATH
    config.DB_PATH = str(db_file)

    new_url = f"sqlite:///{db_file}"
    engine.url = new_url

    yield db_file
    config.DB_PATH = original_db


def test__db__get_session__provides_active_session():
    # Act
    with get_session() as session:
        # Assert
        assert session.is_active


def test__db__sqlite_pragmas__foreign_keys_enabled():
    # Act
    with get_session() as session:
        result = session.exec(text("PRAGMA foreign_keys")).fetchone()
        # Assert
        assert result[0] == 1


def test__db__sqlite_pragmas__wal_mode_enabled():
    # Act
    with get_session() as session:
        result = session.exec(text("PRAGMA journal_mode")).fetchone()
        # Assert
        assert result[0].lower() == "wal"
