import pytest
import responses
from src.api_client import ApiClient
from src.exceptions import ApiServerError, DataNotFoundError


@pytest.fixture
def api_client():
    # Arrange
    client = ApiClient(base_url="https://api.example.com", max_retries=1, backoff_base=0.01)
    yield client
    client.close()


@responses.activate
def test__api_client__get_users__returns_list(api_client):
    # Arrange
    responses.add(responses.GET, "https://api.example.com/users", json=[{"id": 1, "name": "Test"}], status=200)

    # Act
    data = api_client.get_users()

    # Assert
    assert len(data) == 1


@responses.activate
def test__api_client__server_error__retries_and_fails(api_client):
    # Arrange
    responses.add(responses.GET, "https://api.example.com/users", status=500)
    responses.add(responses.GET, "https://api.example.com/users", status=500)

    # Act & Assert
    with pytest.raises(ApiServerError):
        api_client.get_users()


@responses.activate
def test__api_client__server_error__retries_and_succeeds(api_client):
    # Arrange
    responses.add(responses.GET, "https://api.example.com/users", status=500)
    responses.add(responses.GET, "https://api.example.com/users", json=[{"id": 1}], status=200)

    # Act
    data = api_client.get_users()

    # Assert
    assert data[0]["id"] == 1


@responses.activate
def test__api_client__not_found__raises_data_not_found(api_client):
    # Arrange
    responses.add(responses.GET, "https://api.example.com/users", status=404)

    # Act & Assert
    with pytest.raises(DataNotFoundError):
        api_client.get_users()


@responses.activate
def test__api_client__get_posts__returns_list(api_client):
    # Arrange
    responses.add(responses.GET, "https://api.example.com/posts", json=[{"id": 1, "title": "Post"}], status=200)

    # Act
    data = api_client.get_posts()

    # Assert
    assert len(data) == 1


@responses.activate
def test__api_client__get_comments__returns_list(api_client):
    # Arrange
    responses.add(responses.GET, "https://api.example.com/comments", json=[{"id": 1, "body": "Comment"}], status=200)

    # Act
    data = api_client.get_comments()

    # Assert
    assert len(data) == 1


@responses.activate
def test__api_client__bad_request__raises_api_client_error(api_client):
    # Arrange
    from src.exceptions import ApiClientError

    responses.add(responses.GET, "https://api.example.com/users", status=400)

    # Act & Assert
    with pytest.raises(ApiClientError):
        api_client.get_users()
