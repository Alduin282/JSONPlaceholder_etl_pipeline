import logging
from typing import Any, Dict, List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import (
    API_BASE_URL,
    MAX_RETRIES,
    REQUEST_TIMEOUT,
    RETRY_BACKOFF_BASE,
    RETRY_STATUS_CODES,
)
from src.exceptions import ApiError

logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(self) -> None:
        self._base_url = API_BASE_URL
        self._session = requests.Session()

        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=RETRY_BACKOFF_BASE,
            status_forcelist=RETRY_STATUS_CODES,
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

    def __enter__(self) -> "ApiClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._session.close()

    def get_resource(self, resource_name: str) -> List[Dict[str, Any]]:
        url = f"{self._base_url}/{resource_name}"
        try:
            logger.debug("Запрос к API: %s", url)
            response = self._session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            data = response.json()
            logger.info("Успешно получено %d записей для ресурса '%s'", len(data), resource_name)
            return data

        except requests.exceptions.HTTPError as exc:
            status = getattr(exc.response, "status_code", "N/A")
            raise ApiError(f"HTTP ошибка {status} для {resource_name}: {exc}", status_code=status) from exc
        except requests.exceptions.RequestException as exc:
            raise ApiError(f"Ошибка соединения при запросе {resource_name}: {exc}") from exc
