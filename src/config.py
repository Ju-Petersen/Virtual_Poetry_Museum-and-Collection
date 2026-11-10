import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def get_database_url() -> str:
    mysql_url = os.getenv("MYSQL_DATABASE_URL")
    if mysql_url:
        return mysql_url
    sqlite_path = BASE_DIR / "poetry_museum.db"
    return f"sqlite:///{sqlite_path}"
