import pytest
from pydantic import ValidationError
from src.models import User, Comment


@pytest.fixture
def valid_user_data():
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


def test__user_model__valid_data__instantiated(valid_user_data):
    # Act
    user = User.model_validate(valid_user_data)

    # Assert
    assert user.id == 1


def test__user_model__missing_id__raises_validation_error(valid_user_data):
    # Arrange
    del valid_user_data["id"]

    # Act & Assert
    with pytest.raises(ValidationError):
        User.model_validate(valid_user_data)


def test__user_model__none_field__raises_validation_error(valid_user_data):
    # Arrange
    valid_user_data["name"] = None

    # Act & Assert
    with pytest.raises(ValidationError):
        User.model_validate(valid_user_data)


def test__user_model__invalid_email__raises_validation_error(valid_user_data):
    # Arrange
    valid_user_data["email"] = "not-an-email"

    # Act & Assert
    with pytest.raises(ValidationError):
        User.model_validate(valid_user_data)


def test__comment_model__invalid_email__raises_validation_error():
    # Arrange & Act & Assert
    with pytest.raises(ValidationError):
        Comment.model_validate({"id": 1, "postId": 2, "name": "N", "email": "not-an-email", "body": "B"})


def test__user_model__whitespace_name__stripped(valid_user_data):
    # Arrange
    valid_user_data["name"] = "  John  "

    # Act
    user = User.model_validate(valid_user_data)

    # Assert
    assert user.name == "John"
