from pathlib import Path

from backend.app.core.database import get_connection


def migrate_database():
    schema_path = Path(__file__).with_name("schema.sql")

    with get_connection() as connection:
        connection.execute(schema_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    migrate_database()
    print("ExceptionOS database schema is ready.")
