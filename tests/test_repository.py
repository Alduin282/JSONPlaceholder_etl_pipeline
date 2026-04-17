import pytest
from sqlalchemy import text
from sqlmodel import Session, create_engine, SQLModel
from src.repository import Repository
from src.models import User, Post, Comment


@pytest.fixture
def repo():
    # Arrange
    return Repository()


@pytest.fixture
def session(repo):
    # Arrange
    # Для тестов используем базу в памяти
    engine = create_engine("sqlite:///:memory:")
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Схема создается через SQLModel
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


def test__repository__upsert_many__new_data__inserted(repo, session):
    # Arrange
    data = [{"id": 1, "name": "Init", "username": "i", "email": "i@i.com"}]

    # Act
    with session.begin():
        repo.upsert_many(session, User, data)

    # Assert
    row = session.execute(text("SELECT name FROM users WHERE id=1")).fetchone()
    assert row[0] == "Init"


def test__repository__upsert_many__existing_id__updated(repo, session):
    # Arrange
    data1 = [{"id": 1, "name": "Old", "username": "u", "email": "e@e.com"}]
    data2 = [{"id": 1, "name": "New", "username": "u", "email": "e@e.com"}]
    with session.begin():
        repo.upsert_many(session, User, data1)

    # Act
    with session.begin():
        repo.upsert_many(session, User, data2)

    # Assert
    row = session.execute(text("SELECT name FROM users WHERE id=1")).fetchone()
    assert row[0] == "New"


def test__repository__upsert_many__empty_list__returns_zero(repo, session):
    # Act
    result = repo.upsert_many(session, User, [])

    # Assert
    assert result == 0


def test__repository__cascade_delete__user_removed__posts_removed(repo, session):
    # Arrange
    with session.begin():
        repo.upsert_many(session, User, [{"id": 1, "name": "U", "username": "u", "email": "e@e.com"}])
        repo.upsert_many(session, Post, [{"id": 10, "user_id": 1, "title": "T", "body": "B"}])

    # Act
    with session.begin():
        user = session.get(User, 1)
        session.delete(user)

    # Assert
    count = session.execute(text("SELECT COUNT(*) FROM posts WHERE id=10")).fetchone()[0]
    assert count == 0


def test__repository__cascade_delete__post_removed__comments_removed(repo, session):
    # Arrange
    with session.begin():
        repo.upsert_many(session, User, [{"id": 1, "name": "U", "username": "u", "email": "e@e.com"}])
        repo.upsert_many(session, Post, [{"id": 10, "user_id": 1, "title": "T", "body": "B"}])
        repo.upsert_many(session, Comment, [{"id": 100, "post_id": 10, "name": "C", "email": "c@c.com", "body": "B"}])

    # Act
    with session.begin():
        post = session.get(Post, 10)
        session.delete(post)

    # Assert
    count = session.execute(text("SELECT COUNT(*) FROM comments WHERE id=100")).fetchone()[0]
    assert count == 0
