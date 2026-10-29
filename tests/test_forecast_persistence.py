import pytest

psycopg = pytest.importorskip("psycopg")
from backend.database import database_url
from backend.forecast_persistence import save_forecasts

pytestmark = [pytest.mark.db, pytest.mark.skipif(False, reason="placeholder")]


def _available():
    try:
        with psycopg.connect(database_url(), connect_timeout=2):
            return True
    except psycopg.Error:
        return False


pytestmark = [pytest.mark.db, pytest.mark.skipif(not _available(), reason="PostgreSQL is unreachable")]


def test_forecast_upsert_does_not_duplicate_rows():
    frame = __import__("pandas").DataFrame([{ "forecast_date": "2099-01-03", "store_id": "S1", "product_id": "P1", "prediction": 10, "model": "test" }])
    save_forecasts(frame)
    frame.loc[0, "prediction"] = 12
    save_forecasts(frame)
    with psycopg.connect(database_url()) as conn:
        row = conn.execute("SELECT count(*), max(predicted_demand) FROM forecasts WHERE target_week='2099-01-03' AND store_id='S1' AND product_id='P1' AND model_name='test'").fetchone()
        assert row == (1, 12)
