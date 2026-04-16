import pytest
from unittest.mock import MagicMock
from src.loader import Loader
from src.repository import Repository
from src.db import get_connection
from src import config


@pytest.fixture
def mock_api():
    # Arrange
    return MagicMock()


@pytest.fixture
def repo():
    # Arrange
    return Repository()


@pytest.fixture
def test_db(tmp_path):
    # Arrange
    db_file = tmp_path / "test.db"
    original_db = config.DB_PATH
    config.DB_PATH = str(db_file)
    yield db_file
    # Clean up
    config.DB_PATH = original_db


@pytest.fixture
def loader(mock_api, repo, test_db):
    # Arrange
    return Loader(mock_api, repo)


def test__loader__run__creates_tables(loader, mock_api, test_db):
    # Arrange
    mock_api.get_users.return_value = []
    mock_api.get_posts.return_value = []
    mock_api.get_comments.return_value = []

    # Act
    loader.run()

    # Assert
    with get_connection() as conn:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]
        assert "users" in table_names


def test__loader__run__saves_users_successfully(loader, mock_api, test_db):
    # Arrange
    mock_api.get_users.return_value = [
        {
            "id": 1,
            "name": "Leanne Graham",
            "username": "Bret",
            "email": "Sincere@april.biz",
            "address": {"geo": {"lat": "0", "lng": "0"}},
            "company": {"name": "Romaguera-Crona"},
        }
    ]
    mock_api.get_posts.return_value = []
    mock_api.get_comments.return_value = []

    # Act
    loader.run()

    # Assert
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        assert count == 1


def test__loader__single_record_invalid__skips_and_continues(loader, mock_api, test_db):
    # Arrange
    mock_api.get_users.return_value = [
        {"id": 1, "name": "Valid", "username": "v", "email": "v@v.com"},  # Valid
        {"id": 2, "name": "Invalid"},  # Invalid (missing required fields)
    ]
    mock_api.get_posts.return_value = []
    mock_api.get_comments.return_value = []

    # Act
    loader.run()

    # Assert
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        assert count == 1


def test__loader__run__saves_posts_successfully(loader, mock_api, test_db):
    # Arrange
    mock_api.get_users.return_value = [{"id": 1, "name": "U", "username": "u", "email": "u@u.com"}]
    mock_api.get_posts.return_value = [{"id": 1, "userId": 1, "title": "T", "body": "B"}]
    mock_api.get_comments.return_value = []

    # Act
    loader.run()

    # Assert
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        assert count == 1


def test__loader__run__saves_comments_successfully(loader, mock_api, test_db):
    # Arrange
    mock_api.get_users.return_value = [{"id": 1, "name": "U", "username": "u", "email": "u@u.com"}]
    mock_api.get_posts.return_value = [{"id": 1, "userId": 1, "title": "T", "body": "B"}]
    mock_api.get_comments.return_value = [{"id": 1, "postId": 1, "name": "N", "email": "e@e.com", "body": "B"}]

    # Act
    loader.run()

    # Assert
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
        assert count == 1


def test__loader__all_records_invalid__raises_validation_error(loader, mock_api, test_db):
    # Arrange
    from src.exceptions import ValidationError

    mock_api.get_users.return_value = [{"bad": "data"}]

    # Act & Assert
    with pytest.raises(ValidationError):
        loader.run()
