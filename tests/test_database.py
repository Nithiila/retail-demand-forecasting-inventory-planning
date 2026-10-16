import os

import pytest

psycopg = pytest.importorskip("psycopg")

from backend.database import database_url

pytestmark = pytest.mark.db


def postgres_available() -> bool:
    try:
        with psycopg.connect(database_url(), connect_timeout=2):
            return True
    except psycopg.Error:
        return False


pytestmark = pytest.mark.skipif(not postgres_available(), reason="PostgreSQL is unreachable")


def test_database_schema_and_relationships():
    with psycopg.connect(database_url()) as conn:
        rows = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('sales','products','stores','inventory','forecasts')").fetchall()
        assert {row[0] for row in rows} == {"sales", "products", "stores", "inventory", "forecasts"}


def test_database_foreign_keys_exist():
    with psycopg.connect(database_url()) as conn:
        count = conn.execute("SELECT count(*) FROM information_schema.table_constraints WHERE constraint_type='FOREIGN KEY' AND table_name IN ('sales','inventory','forecasts')").fetchone()[0]
        assert count >= 6
