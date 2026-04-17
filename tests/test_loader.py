import pytest
from unittest.mock import MagicMock, patch, ANY
from src.loader import Loader
from src.models import User
from src.exceptions import ValidationError


@pytest.fixture
def mock_api():
    api = MagicMock()
    api.get_resource.return_value = []
    return api


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def loader(mock_api, repo):
    return Loader(mock_api, repo)


def test__loader__run__calls_create_tables(loader, repo):
    # Act
    with patch("src.loader.get_session"):
        loader.run()

    # Assert
    repo.create_tables.assert_called_once()


def test__loader__run__processes_all_entities(loader, mock_api, repo):
    # Act
    with patch("src.loader.get_session"):
        loader.run()

    # Assert
    assert mock_api.get_resource.called
    assert mock_api.get_resource.call_count == len(loader._registry)


def test__loader__validation_error__raises_exception(loader, mock_api):
    # Arrange
    mock_api.get_resource.return_value = [{"invalid": "data"}]

    # Act & Assert
    with patch("src.loader.get_session"):
        with pytest.raises(ValidationError, match="битые"):
            loader.run()


def test__loader__partial_invalid__saves_only_valid(loader, mock_api, repo):
    # Arrange
    valid_user = {
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
    invalid_user = {
        "id": 2,
        "name": "",
        "username": "invalid",
        "email": "invalid@example.com",
    }  # name cannot be empty

    mock_api.get_resource.side_effect = lambda r: (
        [valid_user, invalid_user] if r == "users" else []
    )

    # Act
    with patch("src.loader.get_session"):
        loader.run()

    # Assert
    assert repo.upsert_many.call_count == 1
    repo.upsert_many.assert_any_call(
        ANY,
        User,
        [
            {
                "id": 1,
                "name": "Valid User",
                "username": "valid",
                "email": "valid@example.com",
                "phone": "",
                "website": "",
            }
        ],
    )
