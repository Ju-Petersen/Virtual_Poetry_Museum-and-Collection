from src.config import get_database_url
from src.database import create_database


def test_database_url_defaults_to_sqlite():
    url = get_database_url()
    assert url.startswith("sqlite")


def test_database_tables_can_be_created():
    create_database()
    assert True
