import logging
from typing import Any, Dict

from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from src.api_client import ApiClient
from src.db import get_session, engine
from src.exceptions import ValidationError
from src.models import Comment, Post, User, Address, Company
from src.repository import Repository

logger = logging.getLogger(__name__)


class Loader:
    def __init__(self, api_client: ApiClient, repository: Repository):
        self._api_client = api_client
        self._repository = repository

        self._load_jobs = [
            {
                "resource": "users",
                "model": User,
                "mappings": [
                    (User, self._map_user_base),
                    (Address, self._map_user_address),
                    (Company, self._map_user_company),
                ],
            },
            {
                "resource": "posts",
                "model": Post,
                "mappings": [(Post, self._map_simple)],
            },
            {
                "resource": "comments",
                "model": Comment,
                "mappings": [(Comment, self._map_simple)],
            },
        ]

    def _map_user_base(self, user: User):
        return user.model_dump(exclude={"address", "company"})

    def _map_user_address(self, user: User):
        if not user.address:
            return None
        return {
            "user_id": user.id,
            **user.address.model_dump(exclude={"geo"}),
            "geo_lat": user.address.geo_lat,
            "geo_lng": user.address.geo_lng,
        }

    def _map_user_company(self, user: User):
        if not user.company:
            return None
        return {"user_id": user.id, **user.company.model_dump()}

    def _map_simple(self, model_obj):
        return model_obj.model_dump()

    def run(self) -> None:
        self._repository.create_tables(engine)

        with get_session() as session:
            with session.begin():
                for load_job in self._load_jobs:
                    self._process_entity(session, load_job)

    def _process_entity(self, session: Session, load_job: Dict[str, Any]) -> None:
        resource = load_job["resource"]
        raw_data = self._api_client.get_resource(resource)
        model_class = load_job["model"]

        valid_models = []
        errors_count = 0

        for item in raw_data:
            try:
                valid_models.append(model_class.model_validate(item))
            except PydanticValidationError as e:
                errors_count += 1
                logger.warning("Ошибка в %s: %s", resource, e)

        if raw_data and errors_count == len(raw_data):
            raise ValidationError(f"Все записи {resource} битые")

        for db_model_class, mapper in load_job["mappings"]:
            db_records = [
                record
                for model in valid_models
                if (record := mapper(model)) is not None
            ]
            if db_records:
                self._repository.upsert_many(session, db_model_class, db_records)

        logger.info("Загружено %s: %d записей", resource, len(valid_models))
