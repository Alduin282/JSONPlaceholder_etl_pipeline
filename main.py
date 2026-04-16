"""
main.py — Точка входа в ETL-приложение.

Отвечает за:
- Инициализацию логирования
- Настройку окружения (UNICODE на Windows)
- Сборку зависимостей (ApiClient, Repository)
- Запуск Loader
- Глобальную обработку ошибок
"""

import logging
import sys

from src.api_client import ApiClient
from src.config import LOG_DATE_FORMAT, LOG_FORMAT, LOG_LEVEL
from src.exceptions import (
    ApiError,
    AppError,
    DatabaseError,
    ValidationError,
)
from src.loader import Loader
from src.repository import Repository

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def setup_logging() -> None:
    """Настроить логирование для всего приложения."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Запуск ETL-скрипта JSONPlaceholder -> SQLite")

    try:
        with ApiClient() as api_client:
            repo = Repository()
            loader = Loader(api_client=api_client, repository=repo)
            loader.run()

    except ApiError as exc:
        logger.error(
            "Ошибка API (статус %s): %s",
            getattr(exc, "status_code", "N/A"),
            exc,
        )
        sys.exit(1)

    except ValidationError as exc:
        logger.error("Ошибка валидации данных: %s", exc)
        sys.exit(1)

    except DatabaseError as exc:
        logger.error("Ошибка базы данных: %s", exc)
        sys.exit(1)

    except AppError as exc:
        logger.error("Неожиданная ошибка приложения: %s", exc)
        sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Прервано пользователем (Ctrl+C)")
        sys.exit(0)


if __name__ == "__main__":
    main()
