from typing import Any, List
from pydantic import field_validator, ConfigDict, EmailStr, model_validator
from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int = Field(primary_key=True)
    name: str = Field(index=True)
    username: str = Field(index=True)
    email: EmailStr
    phone: str = ""
    website: str = ""

    address: "Address" = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False},
    )
    company: "Company" = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False},
    )
    posts: List["Post"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    @field_validator("name", "username")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if isinstance(v, str) and not v.strip():
            raise ValueError("Поле не может быть пустой строкой")
        return v.strip() if isinstance(v, str) else v

    @model_validator(mode="before")
    @classmethod
    def validate_relationships(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "address" not in data or data["address"] is None:
                raise ValueError("Поле address обязательно")
            if "company" not in data or data["company"] is None:
                raise ValueError("Поле company обязательно")
        return data

    model_config = ConfigDict(populate_by_name=True)


class Address(SQLModel, table=True):
    __tablename__ = "user_addresses"

    user_id: int = Field(foreign_key="users.id", primary_key=True, ondelete="CASCADE")
    street: str = ""
    suite: str = ""
    city: str = ""
    zipcode: str = ""

    geo_lat: float | None = None
    geo_lng: float | None = None

    user: "User" = Relationship(back_populates="address")

    @model_validator(mode="before")
    @classmethod
    def flatten_geo(cls, data: Any) -> Any:
        if isinstance(data, dict) and "geo" in data:
            geo = data.pop("geo")
            data["geo_lat"] = geo.get("lat")
            data["geo_lng"] = geo.get("lng")
        return data


class Company(SQLModel, table=True):
    __tablename__ = "user_companies"

    user_id: int = Field(foreign_key="users.id", primary_key=True, ondelete="CASCADE")
    name: str = ""
    catch_phrase: str = Field(default="", alias="catchPhrase")
    bs: str = ""

    user: "User" = Relationship(back_populates="company")

    model_config = ConfigDict(populate_by_name=True)


class Post(SQLModel, table=True):
    __tablename__ = "posts"

    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.id", ondelete="CASCADE", alias="userId")
    title: str
    body: str

    user: "User" = Relationship(back_populates="posts")
    comments: List["Comment"] = Relationship(
        back_populates="post", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    @field_validator("title", "body")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if isinstance(v, str) and not v.strip():
            raise ValueError("Поле не может быть пустой строкой")
        return v.strip() if isinstance(v, str) else v

    model_config = ConfigDict(populate_by_name=True)


class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: int = Field(primary_key=True)
    post_id: int = Field(foreign_key="posts.id", ondelete="CASCADE", alias="postId")
    name: str
    email: EmailStr
    body: str

    post: "Post" = Relationship(back_populates="comments")

    @field_validator("name", "body")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if isinstance(v, str) and not v.strip():
            raise ValueError("Поле не может быть пустой строкой")
        return v.strip() if isinstance(v, str) else v

    model_config = ConfigDict(populate_by_name=True)
