import os

import pytest
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from backend.app.core.database import get_connection, get_database_url
from backend.init_db import initialize_database

os.environ["ENABLE_LLM_RECOMMENDATIONS"] = "false"


@pytest.fixture(scope="session", autouse=True)
def test_database():
    original_database_url = get_database_url()
    test_parameters = conninfo_to_dict(original_database_url)
    test_parameters["dbname"] = f"{test_parameters['dbname']}_test"
    os.environ["DATABASE_URL"] = make_conninfo(**test_parameters)

    initialize_database()
    yield

    os.environ["DATABASE_URL"] = original_database_url


@pytest.fixture(autouse=True)
def clean_database(test_database):
    with get_connection() as connection:
        connection.execute(
            """
            TRUNCATE source_lookups, review_corrections, correction_patterns,
                email_imports, audit_events, reviews, erp_orders, source_documents
            RESTART IDENTITY
            """
        )
