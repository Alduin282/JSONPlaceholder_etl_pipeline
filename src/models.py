from pydantic import BaseModel, EmailStr, field_validator


class Geo(BaseModel):
    lat: str = ""
    lng: str = ""


class Address(BaseModel):
    street: str = ""
    suite: str = ""
    city: str = ""
    zipcode: str = ""
    geo: Geo = Geo()

    def to_db_tuple(self, user_id: int) -> tuple:
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
    name: str = ""
    catchPhrase: str = ""
    bs: str = ""

    def to_db_tuple(self, user_id: int) -> tuple:
        return (user_id, self.name, self.catchPhrase, self.bs)


class User(BaseModel):
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
        return (
            self.id,
            self.name,
            self.username,
            str(self.email),
            self.phone,
            self.website,
        )


class Post(BaseModel):
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
        return (self.id, self.userId, self.title, self.body)


class Comment(BaseModel):
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
        return (self.id, self.postId, self.name, str(self.email), self.body)
