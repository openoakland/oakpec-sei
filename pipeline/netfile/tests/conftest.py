import pytest

from ..models import build_tables, destroy_database


@pytest.fixture
def reset_database():
    destroy_database()
    build_tables()
    yield
    destroy_database()
