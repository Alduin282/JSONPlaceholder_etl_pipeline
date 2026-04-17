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

        self._registry = [
            {
                "resource": "users",
                "model": User,
                "storage": [
                    (User, lambda m: m.model_dump(exclude={"address", "company"})),
                    (
                        Address,
                        lambda m: (
                            {
                                "user_id": m.id,
                                **m.address.model_dump(exclude={"geo"}),
                                "geo_lat": m.address.geo_lat,
                                "geo_lng": m.address.geo_lng,
                            }
                            if m.address
                            else None
                        ),
                    ),
                    (Company, lambda m: {"user_id": m.id, **m.company.model_dump()} if m.company else None),
                ],
            },
            {"resource": "posts", "model": Post, "storage": [(Post, lambda m: m.model_dump())]},
            {"resource": "comments", "model": Comment, "storage": [(Comment, lambda m: m.model_dump())]},
        ]

    def run(self) -> None:
        self._repository.create_tables(engine)

        with get_session() as session:
            with session.begin():
                for entity in self._registry:
                    self._process_entity(session, entity)

    def _process_entity(self, session: Session, config: Dict[str, Any]) -> None:
        resource = config["resource"]
        raw_data = self._api_client.get_resource(resource)
        model_cls = config["model"]

        valid_models = []
        errors_count = 0

        for item in raw_data:
            try:
                valid_models.append(model_cls.model_validate(item))
            except PydanticValidationError as e:
                errors_count += 1
                logger.warning("Ошибка в %s: %s", resource, e)

        if raw_data and errors_count == len(raw_data):
            raise ValidationError(f"Все записи {resource} битые")

        for db_class, mapper in config["storage"]:
            # Пропускаем записи, для которых mapper вернул None (например, если нет адреса)
            db_records = [rec for m in valid_models if (rec := mapper(m)) is not None]
            if db_records:
                self._repository.upsert_many(session, db_class, db_records)

        logger.info("Загружено %s: %d записей", resource, len(valid_models))
