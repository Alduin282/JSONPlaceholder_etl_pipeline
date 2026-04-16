"""
models.py — Pydantic v2 схемы для валидации данных из API.

Каждая модель:
- Проверяет типы и обязательные поля
- Задаёт разумные дефолты для необязательных полей
- Предоставляет метод для сериализации в кортеж (для executemany)
"""

from pydantic import BaseModel, EmailStr, field_validator


class Geo(BaseModel):
    """Географические координаты из address.geo."""

    lat: str = ""
    lng: str = ""


class Address(BaseModel):
    """Адрес пользователя. Geo расплющивается в geo_lat / geo_lng."""

    street: str = ""
    suite: str = ""
    city: str = ""
    zipcode: str = ""
    geo: Geo = Geo()

    def to_db_tuple(self, user_id: int) -> tuple:
        """Кортеж для INSERT в таблицу user_addresses."""
        return (
            user_id,
            self.street,
            self.suite,
            self.city,
            self.zipcode,
            self.geo.lat,
            self.geo.lng,
        )


class Company(BaseModel):
    """Компания пользователя."""

    name: str = ""
    catchPhrase: str = ""
    bs: str = ""

    def to_db_tuple(self, user_id: int) -> tuple:
        """Кортеж для INSERT в таблицу user_companies."""
        return (user_id, self.name, self.catchPhrase, self.bs)


class User(BaseModel):
    """Схема пользователя из /users."""

    id: int
    name: str
    username: str
    email: EmailStr
    phone: str = ""
    website: str = ""
    address: Address = Address()
    company: Company = Company()

    @field_validator("name", "username")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Поле не может быть пустой строкой")
        return v.strip()

    def to_db_tuple(self) -> tuple:
        """Кортеж значений для INSERT в таблицу users (без address и company)."""
        return (
            self.id,
            self.name,
            self.username,
            str(self.email),
            self.phone,
            self.website,
        )


class Post(BaseModel):
    """Схема поста из /posts."""

    id: int
    userId: int
    title: str
    body: str

    @field_validator("title", "body")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Поле не может быть пустой строкой")
        return v.strip()

    def to_db_tuple(self) -> tuple:
        """Кортеж значений для INSERT в таблицу posts."""
        return (self.id, self.userId, self.title, self.body)


class Comment(BaseModel):
    """Схема комментария из /comments."""

    id: int
    postId: int
    name: str
    email: EmailStr
    body: str

    @field_validator("name", "body")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Поле не может быть пустой строкой")
        return v.strip()

    def to_db_tuple(self) -> tuple:
        """Кортеж значений для INSERT в таблицу comments."""
        return (self.id, self.postId, self.name, str(self.email), self.body)
