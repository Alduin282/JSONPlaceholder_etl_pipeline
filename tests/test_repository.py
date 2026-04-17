import pytest
import sqlite3
from src.repository import Repository
from src.models import User, Post, Comment
from src.db import get_connection
from src import config


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
def conn(test_db, repo):
    # Arrange
    with get_connection() as c:
        repo.create_tables(c)
        yield c


def test__repository__upsert_users__new_data__inserted(repo, conn):
    # Arrange
    user = User(
        id=1,
        name="Init",
        username="i",
        email="i@i.com",
        address={"geo": {"lat": "0", "lng": "0"}},
        company={"name": "C"},
    )

    # Act
    repo.upsert_users(conn, [user])

    # Assert
    row = conn.execute("SELECT name FROM users WHERE id=1").fetchone()
    assert row["name"] == "Init"


def test__repository__upsert_users__existing_id__updated(repo, conn):
    # Arrange
    user1 = User(id=1, name="Old", username="u", email="e@e.com")
    user2 = User(id=1, name="New", username="u", email="e@e.com")
    repo.upsert_users(conn, [user1])

    # Act
    repo.upsert_users(conn, [user2])

    # Assert
    row = conn.execute("SELECT name FROM users WHERE id=1").fetchone()
    assert row["name"] == "New"


def test__repository__upsert_users__existing_id__updates_all_fields(repo, conn):
    # Arrange
    user1 = User(id=1, name="Old", username="old", email="old@e.com", phone="1", website="old.com")
    user2 = User(id=1, name="New", username="new", email="new@e.com", phone="2", website="new.com")
    repo.upsert_users(conn, [user1])

    # Act
    repo.upsert_users(conn, [user2])

    # Assert
    row = conn.execute("SELECT * FROM users WHERE id=1").fetchone()
    assert row["name"] == "New"
    assert row["username"] == "new"
    assert row["email"] == "new@e.com"
    assert row["phone"] == "2"
    assert row["website"] == "new.com"


def test__repository__upsert_posts__valid_user__inserted(repo, conn):
    # Arrange
    user = User(id=1, name="U", username="u", email="e@e.com")
    repo.upsert_users(conn, [user])
    post = Post(id=10, userId=1, title="T", body="B")

    # Act
    repo.upsert_posts(conn, [post])

    # Assert
    row = conn.execute("SELECT title FROM posts WHERE id=10").fetchone()
    assert row["title"] == "T"


def test__repository__upsert_posts__missing_user__raises_error(repo, conn):
    # Arrange
    post = Post(id=10, userId=99, title="T", body="B")

    # Act & Assert
    with pytest.raises(sqlite3.IntegrityError):
        repo.upsert_posts(conn, [post])


def test__repository__cascade_delete__user_removed__posts_removed(repo, conn):
    # Arrange
    user = User(id=1, name="U", username="u", email="e@e.com")
    repo.upsert_users(conn, [user])
    post = Post(id=10, userId=1, title="T", body="B")
    repo.upsert_posts(conn, [post])

    # Act
    conn.execute("DELETE FROM users WHERE id=1")

    # Assert
    row = conn.execute("SELECT COUNT(*) FROM posts WHERE id=10").fetchone()
    assert row[0] == 0


def test__repository__upsert_user_addresses__valid_user__saved(repo, conn):
    # Arrange
    user = User(
        id=1, name="U", username="u", email="e@e.com", address={"street": "Main St", "geo": {"lat": "1", "lng": "2"}}
    )
    repo.upsert_users(conn, [user])

    # Act
    repo.upsert_user_addresses(conn, [user])

    # Assert
    row = conn.execute("SELECT street FROM user_addresses WHERE user_id=1").fetchone()
    assert row["street"] == "Main St"


def test__repository__upsert_user_companies__valid_user__saved(repo, conn):
    # Arrange
    user = User(id=1, name="U", username="u", email="e@e.com", company={"name": "Big Corp"})
    repo.upsert_users(conn, [user])

    # Act
    repo.upsert_user_companies(conn, [user])

    # Assert
    row = conn.execute("SELECT name FROM user_companies WHERE user_id=1").fetchone()
    assert row["name"] == "Big Corp"


def test__repository__upsert_comments__valid_post__inserted(repo, conn):
    # Arrange
    user = User(id=1, name="U", username="u", email="e@e.com")
    repo.upsert_users(conn, [user])
    post = Post(id=10, userId=1, title="T", body="B")
    repo.upsert_posts(conn, [post])
    comment = Comment(id=100, postId=10, name="N", email="e@e.com", body="Hi")

    # Act
    repo.upsert_comments(conn, [comment])

    # Assert
    row = conn.execute("SELECT body FROM comments WHERE id=100").fetchone()
    assert row["body"] == "Hi"


def test__repository__upsert_comments__missing_post__raises_error(repo, conn):
    # Arrange
    comment = Comment(id=100, postId=999, name="N", email="e@e.com", body="Hi")

    # Act & Assert
    with pytest.raises(sqlite3.IntegrityError):
        repo.upsert_comments(conn, [comment])


def test__repository__upsert_users__empty_list__returns_zero(repo, conn):
    # Act
    result = repo.upsert_users(conn, [])

    # Assert
    assert result == 0


def test__repository__upsert_addresses__empty_list__returns_zero(repo, conn):
    # Act
    result = repo.upsert_user_addresses(conn, [])

    # Assert
    assert result == 0


def test__repository__upsert_companies__empty_list__returns_zero(repo, conn):
    # Act
    result = repo.upsert_user_companies(conn, [])

    # Assert
    assert result == 0


def test__repository__upsert_posts__empty_list__returns_zero(repo, conn):
    # Act
    result = repo.upsert_posts(conn, [])

    # Assert
    assert result == 0


def test__repository__upsert_comments__empty_list__returns_zero(repo, conn):
    # Act
    result = repo.upsert_comments(conn, [])

    # Assert
    assert result == 0


def test__repository__cascade_delete__user_removed__comments_removed(repo, conn):
    # Arrange
    user = User(id=1, name="U", username="u", email="e@e.com")
    repo.upsert_users(conn, [user])
    post = Post(id=10, userId=1, title="T", body="B")
    repo.upsert_posts(conn, [post])
    comment = Comment(id=100, postId=10, name="N", email="e@e.com", body="Hi")
    repo.upsert_comments(conn, [comment])

    # Act
    conn.execute("DELETE FROM users WHERE id=1")

    # Assert
    row = conn.execute("SELECT COUNT(*) FROM comments WHERE id=100").fetchone()
    assert row[0] == 0
