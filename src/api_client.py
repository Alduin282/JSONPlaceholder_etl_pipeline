from __future__ import annotations

import logging
import time
from typing import Any

import requests

from src.config import (
    API_BASE_URL,
    MAX_RETRIES,
    REQUEST_TIMEOUT,
    RETRY_BACKOFF_BASE,
    RETRY_STATUS_CODES,
)
from src.exceptions import ApiClientError, ApiServerError, DataNotFoundError

logger = logging.getLogger(__name__)


class ApiClient:

    def __init__(
        self,
        base_url: str = API_BASE_URL,
        timeout: int = REQUEST_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        backoff_base: float = RETRY_BACKOFF_BASE,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._session = requests.Session()

    def get_users(self) -> list[dict[str, Any]]:
        return self._get("/users")

    def get_posts(self) -> list[dict[str, Any]]:
        return self._get("/posts")

    def get_comments(self) -> list[dict[str, Any]]:
        return self._get("/comments")

    def _get(self, endpoint: str) -> list[dict[str, Any]]:
        url = f"{self._base_url}{endpoint}"
        last_exception: Exception | None = None

        for attempt in range(self._max_retries + 1):
            if attempt > 0:
                delay = self._backoff_base * (2 ** (attempt - 1))
                logger.debug(
                    "Retry %d/%d для %s: ожидание %.1fс",
                    attempt,
                    self._max_retries,
                    url,
                    delay,
                )
                time.sleep(delay)

            try:
                logger.debug("GET %s (попытка %d/%d)", url, attempt + 1, self._max_retries + 1)
                response = self._session.get(url, timeout=self._timeout)
                return self._handle_response(response, url)

            except (requests.Timeout, requests.ConnectionError) as exc:
                logger.warning(
                    "Сетевая ошибка при GET %s (попытка %d/%d): %s",
                    url,
                    attempt + 1,
                    self._max_retries + 1,
                    exc,
                )
                last_exception = exc

            except (DataNotFoundError, ApiClientError):
                raise

            except ApiServerError as exc:
                last_exception = exc

        raise ApiServerError(
            f"Не удалось получить {url} после {self._max_retries + 1} попыток. " f"Последняя ошибка: {last_exception}"
        ) from last_exception

    @staticmethod
    def _handle_response(response: requests.Response, url: str) -> list[dict[str, Any]]:
        status = response.status_code

        if status == 200:
            data = response.json()
            if not isinstance(data, list):
                raise ApiClientError(
                    f"Ожидался список, получен {type(data).__name__} от {url}",
                    status_code=status,
                )
            return data

        if status == 404:
            raise DataNotFoundError(f"Ресурс не найден: {url}", status_code=status)

        if status in RETRY_STATUS_CODES:
            raise ApiServerError(f"Сервер вернул {status} для {url}", status_code=status)

        if 400 <= status < 500:
            raise ApiClientError(f"Ошибка клиента {status} для {url}", status_code=status)

        raise ApiServerError(f"Ошибка сервера {status} для {url}", status_code=status)

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> ApiClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
