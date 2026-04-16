import pytest
from pydantic import ValidationError
from src.models import User, Post, Comment, Address, Company, Geo


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
    user = User(**valid_user_data)

    # Assert
    assert user.id == 1


def test__user_model__missing_id__raises_validation_error(valid_user_data):
    # Arrange
    del valid_user_data["id"]

    # Act & Assert
    with pytest.raises(ValidationError):
        User(**valid_user_data)


def test__user_model__none_field__raises_validation_error(valid_user_data):
    # Arrange
    valid_user_data["name"] = None

    # Act & Assert
    with pytest.raises(ValidationError):
        User(**valid_user_data)


def test__user_model__invalid_email__raises_validation_error(valid_user_data):
    # Arrange
    valid_user_data["email"] = "not-an-email"

    # Act & Assert
    with pytest.raises(ValidationError):
        User(**valid_user_data)


def test__address_model__to_db_tuple__returns_flattened_geo():
    # Arrange
    addr = Address(street="S", suite="Su", city="C", zipcode="Z", geo=Geo(lat="1.2", lng="3.4"))

    # Act
    result = addr.to_db_tuple(user_id=10)

    # Assert
    assert result == (10, "S", "Su", "C", "Z", "1.2", "3.4")


def test__company_model__to_db_tuple__returns_correct_tuple():
    # Arrange
    comp = Company(name="N", catchPhrase="CP", bs="BS")

    # Act
    result = comp.to_db_tuple(user_id=10)

    # Assert
    assert result == (10, "N", "CP", "BS")


def test__post_model__valid_data__returns_tuple():
    # Arrange
    post = Post(id=1, userId=2, title="T", body="B")

    # Act
    result = post.to_db_tuple()

    # Assert
    assert result == (1, 2, "T", "B")


def test__comment_model__valid_email__accepted():
    # Arrange
    comment = Comment(id=1, postId=2, name="N", email="test@test.com", body="B")

    # Act
    result = comment.to_db_tuple()

    # Assert
    assert result[3] == "test@test.com"


def test__comment_model__invalid_email__raises_validation_error():
    # Arrange & Act & Assert
    with pytest.raises(ValidationError):
        Comment(id=1, postId=2, name="N", email="not-an-email", body="B")


def test__user_model__whitespace_name__stripped(valid_user_data):
    # Arrange
    valid_user_data["name"] = "  John  "

    # Act
    user = User(**valid_user_data)

    # Assert
    assert user.name == "John"
