from pathlib import Path

from backend.app.core.database import create_database_if_missing, get_connection


def initialize_database():
    schema_path = Path(__file__).with_name("schema.sql")

    create_database_if_missing()

    with get_connection() as connection:
        connection.execute(schema_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    initialize_database()
    print("ExceptionOS database initialized.")
