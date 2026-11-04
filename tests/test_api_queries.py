import pytest

psycopg = pytest.importorskip("psycopg")
from fastapi.testclient import TestClient
from backend.database import database_url
from backend.main import app

pytestmark = pytest.mark.db


def available():
    try:
        with psycopg.connect(database_url(), connect_timeout=2): return True
    except psycopg.Error: return False


pytestmark = [pytest.mark.db, pytest.mark.skipif(not available(), reason="PostgreSQL is unreachable")]


def test_products_stores_and_forecast_filters_and_pagination():
    client = TestClient(app)
    assert client.get("/api/v1/products", params={"page": 1, "limit": 10}).status_code == 200
    assert client.get("/api/v1/stores", params={"page": 1, "limit": 10}).status_code == 200
    response = client.get("/api/v1/forecasts", params={"limit": 10})
    assert response.status_code == 200
    assert "items" in response.json()
