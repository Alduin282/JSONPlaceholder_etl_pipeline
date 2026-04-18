import logging
from typing import Any, Dict

from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from src.api_client import ApiClient
from src.db import get_session, engine
from src.exceptions import ValidationError
from src.models import Comment, Post, User, Address, Company
from src.repository import BaseRepository, SQLiteRepository

logger = logging.getLogger(__name__)


def get_repository(db_url: str) -> BaseRepository:
    if db_url.startswith("sqlite"):
        return SQLiteRepository()

    raise ValueError(f"Неподдерживаемая база данных: {db_url}")


class Loader:
    def __init__(self, api_client: ApiClient, repository: BaseRepository):
        self._api_client = api_client
        self._repository = repository

        self._load_jobs = [
            {
                "resource": "users",
                "model": User,
                "mappings": [
                    {"db_model": User, "mapper": self._map_parent},
                    {
                        "resource": "address",
                        "db_model": Address,
                        "mapper": self._map_nested,
                        "attribute": "address",
                        "fk_field": "user_id",
                    },
                    {
                        "resource": "company",
                        "db_model": Company,
                        "mapper": self._map_nested,
                        "attribute": "company",
                        "fk_field": "user_id",
                    },
                ],
            },
            {
                "resource": "posts",
                "model": Post,
                "mappings": [{"db_model": Post, "mapper": self._map_parent}],
            },
            {
                "resource": "comments",
                "model": Comment,
                "mappings": [{"db_model": Comment, "mapper": self._map_parent}],
            },
        ]

    def _map_parent(self, model_obj, load_job, _mapping):
        nested_attributes = {
            mapping["attribute"]
            for mapping in load_job["mappings"]
            if "attribute" in mapping
        }
        return model_obj.model_dump(exclude=nested_attributes)

    def _map_nested(self, model_obj, _load_job, mapping):
        nested_model = getattr(model_obj, mapping["attribute"], None)
        if not nested_model:
            return None

        parent_key = mapping.get("parent_key", "id")
        return {
            mapping["fk_field"]: getattr(model_obj, parent_key),
            **nested_model.model_dump(),
        }

    def _validate_model(self, model_class, item, load_job):
        model = model_class.model_validate(item)

        for mapping in load_job["mappings"]:
            resource = mapping.get("resource")
            if not resource or item.get(resource) is None:
                continue

            parent_key = mapping.get("parent_key", "id")
            nested_item = {
                mapping["fk_field"]: getattr(model, parent_key),
                **item[resource],
            }
            setattr(model, mapping["attribute"], mapping["db_model"].model_validate(nested_item))

        return model

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
                valid_models.append(self._validate_model(model_class, item, load_job))
            except PydanticValidationError as e:
                errors_count += 1
                logger.warning("Ошибка в %s: %s", resource, e)

        if raw_data and errors_count == len(raw_data):
            raise ValidationError(f"Все записи {resource} битые")

        for mapping in load_job["mappings"]:
            db_model_class = mapping["db_model"]
            mapper = mapping["mapper"]
            db_records = [
                record
                for model in valid_models
                if (record := mapper(model, load_job, mapping)) is not None
            ]
            if db_records:
                self._repository.upsert_many(session, db_model_class, db_records)

        logger.info("Загружено %s: %d записей", resource, len(valid_models))
