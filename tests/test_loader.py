import pytest
from unittest.mock import MagicMock, patch, ANY
from src.loader import Loader
from src.repository import BaseRepository
from src.models import User, Address, Company
from src.exceptions import ValidationError


@pytest.fixture
def mock_api():
    api = MagicMock()
    api.get_resource.return_value = []
    return api


@pytest.fixture
def repo():
    return MagicMock(spec=BaseRepository)


@pytest.fixture
def loader(mock_api, repo):
    return Loader(mock_api, repo)


@pytest.fixture
def valid_user_raw():
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
def expected_user_record():
    return {
        "id": 1,
        "name": "Valid User",
        "username": "valid",
        "email": "valid@example.com",
        "phone": "",
        "website": "",
    }


@pytest.fixture
def expected_address_record(valid_user_raw):
    address = valid_user_raw["address"]
    return {
        "user_id": valid_user_raw["id"],
        "street": address["street"],
        "suite": address["suite"],
        "city": address["city"],
        "zipcode": address["zipcode"],
        "geo_lat": address["geo"]["lat"],
        "geo_lng": address["geo"]["lng"],
    }


@pytest.fixture
def expected_company_record(valid_user_raw):
    company = valid_user_raw["company"]
    return {
        "user_id": valid_user_raw["id"],
        "name": company["name"],
        "catch_phrase": company["catchPhrase"],
        "bs": company["bs"],
    }


def assert_upsert_called(repo, model_class, expected_records):
    repo.upsert_many.assert_any_call(ANY, model_class, expected_records)


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
    assert mock_api.get_resource.call_count == len(loader._load_jobs)


def test__loader__validation_error__raises_exception(loader, mock_api):
    # Arrange
    mock_api.get_resource.return_value = [{"invalid": "data"}]

    # Act & Assert
    with patch("src.loader.get_session"):
        with pytest.raises(ValidationError, match="битые"):
            loader.run()


def test__loader__partial_invalid__saves_only_valid(
    loader,
    mock_api,
    repo,
    valid_user_raw,
    expected_user_record,
    expected_address_record,
    expected_company_record,
):
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
    loader, mock_api, repo, valid_user_raw, expected_address_record, expected_company_record
):
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
