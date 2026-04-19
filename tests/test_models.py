from typing import Any

import pytest
from pydantic import ValidationError
from src.models import User, Post, Comment, Address


@pytest.fixture
def valid_user_data() -> dict[str, Any]:
    # Arrange
    return {
        "id": 1,
        "name": "John Doe",
        "username": "johnd",
        "email": "john@example.com",
        "phone": "123-456",
        "website": "example.com",
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
def valid_post_data() -> dict[str, Any]:
    # Arrange
    return {
        "id": 1,
        "userId": 1,
        "title": "Valid Title",
        "body": "Valid Body",
    }


@pytest.fixture
def valid_comment_data() -> dict[str, Any]:
    # Arrange
    return {
        "id": 1,
        "postId": 1,
        "name": "Valid Name",
        "email": "valid@example.com",
        "body": "Valid Body",
    }


def test__user_model__valid_data__instantiated(valid_user_data: dict[str, Any]) -> None:
    # Act
    user = User.model_validate(valid_user_data)

    # Assert
    assert user.id == 1


def test__user_model__missing_id__raises_validation_error(
    valid_user_data: dict[str, Any],
) -> None:
    # Arrange
    del valid_user_data["id"]

    # Act & Assert
    with pytest.raises(ValidationError):
        User.model_validate(valid_user_data)


def test__user_model__none_field__raises_validation_error(
    valid_user_data: dict[str, Any],
) -> None:
    # Arrange
    valid_user_data["name"] = None

    # Act & Assert
    with pytest.raises(ValidationError):
        User.model_validate(valid_user_data)


def test__user_model__invalid_email__raises_validation_error(
    valid_user_data: dict[str, Any],
) -> None:
    # Arrange
    valid_user_data["email"] = "not-an-email"

    # Act & Assert
    with pytest.raises(ValidationError):
        User.model_validate(valid_user_data)


def test__comment_model__invalid_email__raises_validation_error() -> None:
    # Arrange & Act & Assert
    with pytest.raises(ValidationError):
        Comment.model_validate(
            {"id": 1, "postId": 2, "name": "N", "email": "not-an-email", "body": "B"}
        )


def test__user_model__empty_name__raises_error(valid_user_data: dict[str, Any]) -> None:
    # Arrange
    valid_user_data["name"] = "   "

    # Act & Assert
    with pytest.raises(ValidationError):
        User.model_validate(valid_user_data)


def test__user_model__empty_address__raises_error(
    valid_user_data: dict[str, Any],
) -> None:
    # Arrange
    valid_user_data["address"] = None

    # Act & Assert
    with pytest.raises(ValidationError):
        User.model_validate(valid_user_data)


def test__post_model__empty_title__raises_error(valid_post_data: dict[str, Any]) -> None:
    # Arrange
    valid_post_data["title"] = ""

    # Act & Assert
    with pytest.raises(ValidationError):
        Post.model_validate(valid_post_data)


def test__comment_model__empty_body__raises_error(
    valid_comment_data: dict[str, Any],
) -> None:
    # Arrange
    valid_comment_data["body"] = " \n "

    # Act & Assert
    with pytest.raises(ValidationError):
        Comment.model_validate(valid_comment_data)


def test__address_model__flatten_geo__maps_lat_lng() -> None:
    # Arrange
    data = {
        "user_id": 1,
        "street": "S",
        "geo": {"lat": "1.23", "lng": "4.56"},
    }

    # Act
    address = Address.model_validate(data)

    # Assert
    assert address.geo_lat == 1.23
    assert address.geo_lng == 4.56
