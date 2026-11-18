from unittest.mock import patch
from fastapi.testclient import TestClient


def test_health_check_success(client: TestClient):
    """Test health check returns 200 and status ok when DB is connected."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_api_v1(client: TestClient):
    """Test health check under /api/v1 prefix."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_db_failure(client: TestClient):
    """Test health check returns 503 if database connection fails."""
    with patch("app.api.v1.health.check_db_connection", return_value=False):
        response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data.get("status") == "error"
        assert "Database connection failed" in data.get("detail", "")
