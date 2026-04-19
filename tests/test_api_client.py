from typing import Iterator

import pytest
import responses
from requests.exceptions import ConnectionError
from src.api_client import ApiClient
from src.exceptions import ApiError


@pytest.fixture
def api_client() -> Iterator[ApiClient]:
    # Arrange
    with ApiClient() as client:
        yield client


@responses.activate
def test__api_client__get_resource__success(api_client: ApiClient) -> None:
    # Arrange
    mock_data = [{"id": 1, "name": "Test"}]
    responses.add(responses.GET, "https://jsonplaceholder.typicode.com/users", json=mock_data, status=200)

    # Act
    data = api_client.get_resource("users")

    # Assert
    assert data == mock_data


@responses.activate
def test__api_client__get_resource__retries_on_500(api_client: ApiClient) -> None:
    # Arrange
    responses.add(responses.GET, "https://jsonplaceholder.typicode.com/users", status=500)
    responses.add(responses.GET, "https://jsonplaceholder.typicode.com/users", json=[], status=200)

    # Act
    data = api_client.get_resource("users")

    # Assert
    assert data == []
    assert len(responses.calls) == 2


@responses.activate
def test__api_client__get_resource__404_raises_api_error(api_client: ApiClient) -> None:
    # Arrange
    responses.add(responses.GET, "https://jsonplaceholder.typicode.com/users", status=404)

    # Act & Assert
    with pytest.raises(ApiError, match="404"):
        api_client.get_resource("users")


@responses.activate
def test__api_client__get_resource__timeout_raises_api_error(
    api_client: ApiClient,
) -> None:
    # Arrange
    responses.add(responses.GET, "https://jsonplaceholder.typicode.com/users", body=ConnectionError("Timeout"))

    # Act & Assert
    with pytest.raises(ApiError, match="Ошибка соединения"):
        api_client.get_resource("users")
