
from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_api_initializes_and_health_is_preserved():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_invalid_forecast_payload_has_consistent_error():
    response = client.post("/api/v1/forecasts", json={"forecasts": [{"prediction": -1}]})
    assert response.status_code == 422
    assert response.json()["detail"] == "Request validation failed"
