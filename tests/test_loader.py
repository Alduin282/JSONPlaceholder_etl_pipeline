from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
import pytest
from unittest.mock import MagicMock, patch, ANY
from sqlalchemy.engine import Engine
from sqlalchemy import event, text
from sqlmodel import Session, create_engine
from src.loader import Loader
from src.repository import BaseRepository, SQLiteRepository
from src.models import User, Address, Company, Post, Comment
from src.exceptions import ValidationError


@pytest.fixture
def mock_api() -> MagicMock:
    api = MagicMock()
    api.get_resource.return_value = []
    return api


@pytest.fixture
def repo() -> MagicMock:
    return MagicMock(spec=BaseRepository)


@pytest.fixture
def loader(mock_api: MagicMock, repo: MagicMock) -> Loader:
    return Loader(mock_api, repo)


@pytest.fixture
def valid_user_raw() -> dict[str, Any]:
    return {
        "id": 1,
        "name": "Valid User",
        "username": "valid",
        "email": "valid@example.com",
        "address": {
            "street": "Kulas Light",
            "suite": "Apt. 556",
            "city": "Gwenborough",
            "zipcode": "92998-3874",
            "geo": {"lat": "-37.3159", "lng": "81.1496"},
        },
        "company": {
            "name": "Romaguera-Crona",
            "catchPhrase": "Multi-layered client-server neural-net",
            "bs": "harness real-time e-markets",
        },
    }


@pytest.fixture
def valid_post_raw(valid_user_raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": 10,
        "userId": valid_user_raw["id"],
        "title": "Post title",
        "body": "Post body",
    }


@pytest.fixture
def valid_comment_raw(valid_post_raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": 100,
        "postId": valid_post_raw["id"],
        "name": "Comment name",
        "email": "comment@example.com",
        "body": "Comment body",
    }


@pytest.fixture
def full_api_payload(
    valid_user_raw: dict[str, Any],
    valid_post_raw: dict[str, Any],
    valid_comment_raw: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    return {
        "users": [valid_user_raw],
        "posts": [valid_post_raw],
        "comments": [valid_comment_raw],
    }


@pytest.fixture
def expected_user_record() -> dict[str, Any]:
    return {
        "id": 1,
        "name": "Valid User",
        "username": "valid",
        "email": "valid@example.com",
        "phone": "",
        "website": "",
    }


@pytest.fixture
def expected_address_record(valid_user_raw: dict[str, Any]) -> dict[str, Any]:
    address = valid_user_raw["address"]
    return {
        "user_id": valid_user_raw["id"],
        "street": address["street"],
        "suite": address["suite"],
        "city": address["city"],
        "zipcode": address["zipcode"],
        "geo_lat": float(address["geo"]["lat"]),
        "geo_lng": float(address["geo"]["lng"]),
    }


@pytest.fixture
def expected_company_record(valid_user_raw: dict[str, Any]) -> dict[str, Any]:
    company = valid_user_raw["company"]
    return {
        "user_id": valid_user_raw["id"],
        "name": company["name"],
        "catch_phrase": company["catchPhrase"],
        "bs": company["bs"],
    }


def assert_upsert_called(
    repo: MagicMock, model_class: type[Any], expected_records: list[dict[str, Any]]
) -> None:
    repo.upsert_many.assert_any_call(ANY, model_class, expected_records)


@pytest.fixture
def sqlite_test_engine(tmp_path: Path) -> Engine:
    db_file = tmp_path / "loader-test.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def test__loader__run__calls_create_tables(loader: Loader, repo: MagicMock) -> None:
    # Act
    with patch("src.loader.get_session"):
        loader.run()

    # Assert
    repo.create_tables.assert_called_once()


def test__loader__run__processes_all_entities(
    loader: Loader, mock_api: MagicMock, repo: MagicMock
) -> None:
    # Act
    with patch("src.loader.get_session"):
        loader.run()

    # Assert
    assert mock_api.get_resource.called
    assert mock_api.get_resource.call_count == len(loader._load_jobs)


def test__loader__validation_error__raises_exception(
    loader: Loader, mock_api: MagicMock
) -> None:
    # Arrange
    mock_api.get_resource.return_value = [{"invalid": "data"}]

    # Act & Assert
    with patch("src.loader.get_session"):
        with pytest.raises(ValidationError, match="битые"):
            loader.run()


def test__loader__partial_invalid__saves_only_valid(
    loader: Loader,
    mock_api: MagicMock,
    repo: MagicMock,
    valid_user_raw: dict[str, Any],
    expected_user_record: dict[str, Any],
    expected_address_record: dict[str, Any],
    expected_company_record: dict[str, Any],
) -> None:
    # Arrange
    invalid_user = {"id": 2, "name": "", "username": "inv", "email": "i@e.com"}
    mock_api.get_resource.side_effect = lambda r: ([valid_user_raw, invalid_user] if r == "users" else [])

    # Act
    with patch("src.loader.get_session"):
        loader.run()

    # Assert
    assert repo.upsert_many.call_count == 3
    assert_upsert_called(repo, User, [expected_user_record])
    assert_upsert_called(repo, Address, [expected_address_record])
    assert_upsert_called(repo, Company, [expected_company_record])


def test__loader__users__loads_address_and_company(
    loader: Loader,
    mock_api: MagicMock,
    repo: MagicMock,
    valid_user_raw: dict[str, Any],
    expected_address_record: dict[str, Any],
    expected_company_record: dict[str, Any],
) -> None:
    # Arrange
    mock_api.get_resource.side_effect = (
        lambda resource: [valid_user_raw] if resource == "users" else []
    )

    # Act
    with patch("src.loader.get_session"):
        loader.run()

    # Assert
    assert_upsert_called(repo, Address, [expected_address_record])
    assert_upsert_called(repo, Company, [expected_company_record])


def test__loader__run__preserves_resource_and_table_order(
    loader: Loader,
    mock_api: MagicMock,
    repo: MagicMock,
    full_api_payload: dict[str, list[dict[str, Any]]],
) -> None:
    # Arrange
    mock_api.get_resource.side_effect = lambda resource: full_api_payload[resource]

    # Act
    with patch("src.loader.get_session"):
        loader.run()

    # Assert
    assert [call.args[0] for call in mock_api.get_resource.call_args_list] == [
        "users",
        "posts",
        "comments",
    ]
    assert [call.args[1] for call in repo.upsert_many.call_args_list] == [
        User,
        Address,
        Company,
        Post,
        Comment,
    ]


def test__loader__run_twice__does_not_create_duplicates(
    full_api_payload: dict[str, list[dict[str, Any]]],
    sqlite_test_engine: Engine,
) -> None:
    # Arrange
    api_client = MagicMock()
    api_client.get_resource.side_effect = lambda resource: full_api_payload[resource]
    loader = Loader(api_client, SQLiteRepository())

    @contextmanager
    def test_session() -> Iterator[Session]:
        with Session(sqlite_test_engine) as session:
            yield session

    # Act
    with (
        patch("src.loader.engine", sqlite_test_engine),
        patch("src.loader.get_session", test_session),
    ):
        loader.run()
        loader.run()

    # Assert
    with Session(sqlite_test_engine) as session:
        assert session.exec(text("SELECT COUNT(*) FROM users")).one()[0] == 1
        assert session.exec(text("SELECT COUNT(*) FROM user_addresses")).one()[0] == 1
        assert session.exec(text("SELECT COUNT(*) FROM user_companies")).one()[0] == 1
        assert session.exec(text("SELECT COUNT(*) FROM posts")).one()[0] == 1
        assert session.exec(text("SELECT COUNT(*) FROM comments")).one()[0] == 1
