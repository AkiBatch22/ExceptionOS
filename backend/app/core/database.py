import os

import psycopg
from dotenv import load_dotenv
from psycopg.conninfo import conninfo_to_dict
from psycopg import sql


load_dotenv()


def get_connection():
    return psycopg.connect(get_database_url())


def get_database_url():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    return database_url


def create_database_if_missing():
    connection_parameters = conninfo_to_dict(get_database_url())
    database_name = connection_parameters.get("dbname")

    if not database_name:
        raise RuntimeError("DATABASE_URL must include a database name")

    maintenance_parameters = connection_parameters.copy()
    maintenance_parameters["dbname"] = "postgres"

    with psycopg.connect(**maintenance_parameters, autocommit=True) as connection:
        database_exists = connection.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (database_name,),
        ).fetchone()

        if database_exists is None:
            connection.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(database_name)
                )
            )
