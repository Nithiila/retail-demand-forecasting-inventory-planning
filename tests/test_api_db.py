import pytest

psycopg = pytest.importorskip("psycopg")
from fastapi.testclient import TestClient

from backend.database import database_url
from backend.main import app

pytestmark = pytest.mark.db


def _available():
    try:
        with psycopg.connect(database_url(), connect_timeout=2):
            return True
    except psycopg.Error:
        return False


pytestmark = [pytest.mark.db, pytest.mark.skipif(not _available(), reason="PostgreSQL is unreachable")]


def test_forecast_endpoint_persists_valid_payload():
    response = TestClient(app).post("/api/v1/forecasts", json={"forecasts": [{"forecast_date": "2099-01-03", "store_id": "S1", "product_id": "P1", "prediction": 10, "model": "test"}]})
    assert response.status_code == 201
    assert response.json() == {"saved": 1}
