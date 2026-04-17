import pytest
from unittest.mock import MagicMock, patch
from src.loader import Loader
from src.models import User, Address, Company
from src.exceptions import ValidationError


@pytest.fixture
def mock_api():
    # Arrange
    api = MagicMock()
    api.get_resource.return_value = []
    return api


@pytest.fixture
def repo():
    # Arrange
    return MagicMock()


@pytest.fixture
def loader(mock_api, repo):
    # Arrange
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
    assert mock_api.get_resource.call_count >= 1


def test__loader__validation_error__raises_exception(loader, mock_api):
    # Arrange
    mock_api.get_resource.return_value = [{"invalid": "data"}]

    # Act & Assert
    with patch("src.loader.get_session"):
        with pytest.raises(ValidationError, match="битые"):
            loader.run()


def test__loader__partial_invalid__saves_only_valid(loader, mock_api, repo):
    # Arrange
    mock_api.get_resource.side_effect = lambda r: (
        [{"id": 1, "name": "V", "username": "v", "email": "v@v.com"}] if r == "users" else []  # Valid
    )

    # Act
    with patch("src.loader.get_session") as mock_get_session:
        mock_session = mock_get_session.return_value.__enter__.return_value
        loader.run()

    # Assert
    found_user_upsert = False
    for call in repo.upsert_many.call_args_list:
        if call[0][1] == User:
            assert len(call[0][2]) == 1
            found_user_upsert = True
    assert found_user_upsert
