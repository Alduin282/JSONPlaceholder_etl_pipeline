import logging
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH: str = os.getenv("DB_PATH", str(BASE_DIR / "jsonplaceholder.db"))
DATABASE_URL: str = f"sqlite:///{DB_PATH}"
SQL_ECHO: bool = False

API_BASE_URL: str = "https://jsonplaceholder.typicode.com"

REQUEST_TIMEOUT: int = 30

MAX_RETRIES: int = 3
RETRY_BACKOFF_BASE: float = 1.0

RETRY_STATUS_CODES: set[int] = {429, 500, 503}

LOG_LEVEL: int = logging.INFO
LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
