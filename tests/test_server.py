
from fastapi.testclient import TestClient

from server.main import app

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from server.database import get_db
from server.security import verify_api_key

client = TestClient(app)


def test_health_check():
    """Проверяет доступность API."""

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_metric_without_api_key():
    """Проверяет отказ в доступе без API-ключа."""

    metric = {
        "hostname": "TEST-PC",
        "cpu_percent": 25.0,
        "ram_percent": 50.0,
        "disk_free_gb": 100.0,
        "uptime_seconds": 3600.0,
    }

    response = client.post(
        "/metrics",
        json=metric,
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid or missing API key"
    }

def test_create_metric_with_invalid_api_key():
    """Проверяет отказ при неправильном API-ключе."""

    metric = {
        "hostname": "TEST-PC",
        "cpu_percent": 25.0,
        "ram_percent": 50.0,
        "disk_free_gb": 100.0,
        "uptime_seconds": 3600.0,
    }

    response = client.post(
        "/metrics",
        json=metric,
        headers={"X-API-Key": "wrong-api-key"},
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid or missing API key"
    }

def test_create_metric_success():
    """Проверяет успешный POST без записи в PostgreSQL."""

    fake_db = MagicMock()

    def fake_refresh(metric):
        metric.id = 1
        metric.timestamp = datetime.now(timezone.utc)

    fake_db.refresh.side_effect = fake_refresh

    def override_get_db():
        yield fake_db

    def override_api_key():
        return "test-key"

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_api_key] = override_api_key

    metric = {
        "hostname": "TEST-PC",
        "cpu_percent": 25.0,
        "ram_percent": 50.0,
        "disk_free_gb": 100.0,
        "uptime_seconds": 3600.0,
    }

    try:
        response = client.post(
            "/metrics",
            json=metric,
            headers={"X-API-Key": "test-key"},
        )

        assert response.status_code == 201

        data = response.json()

        assert data["hostname"] == "TEST-PC"
        assert data["cpu_percent"] == 25.0
        assert data["id"] == 1
        assert "timestamp" in data

        fake_db.add.assert_called_once()
        fake_db.commit.assert_called_once()
        fake_db.refresh.assert_called_once()

    finally:
        app.dependency_overrides.clear()

def test_create_metric_invalid_cpu():
    """Проверяет отклонение недопустимой загрузки CPU."""

    def override_api_key():
        return "test-key"

    app.dependency_overrides[verify_api_key] = override_api_key

    metric = {
        "hostname": "TEST-PC",
        "cpu_percent": 150.0,
        "ram_percent": 50.0,
        "disk_free_gb": 100.0,
        "uptime_seconds": 3600.0,
    }

    try:
        response = client.post(
            "/metrics",
            json=metric,
            headers={"X-API-Key": "test-key"},
        )

        assert response.status_code == 422

        errors = response.json()["detail"]

        assert any(
            "cpu_percent" in error["loc"]
            for error in errors
        )

    finally:
        app.dependency_overrides.clear()

def test_create_metric_invalid_ram():
    """Проверяет отклонение отрицательного значения RAM."""

    def override_api_key():
        return "test-key"

    app.dependency_overrides[verify_api_key] = override_api_key

    metric = {
        "hostname": "TEST-PC",
        "cpu_percent": 25.0,
        "ram_percent": -20.0,
        "disk_free_gb": 100.0,
        "uptime_seconds": 3600.0,
    }

    try:
        response = client.post(
            "/metrics",
            json=metric,
            headers={"X-API-Key": "test-key"},
        )

        assert response.status_code == 422

        errors = response.json()["detail"]

        assert any(
            "ram_percent" in error["loc"]
            for error in errors
        )

    finally:
        app.dependency_overrides.clear()

def test_create_metric_invalid_ram():
    """Проверяет отклонение отрицательного значения RAM."""

    def override_api_key():
        return "test-key"

    app.dependency_overrides[verify_api_key] = override_api_key

    metric = {
        "hostname": "TEST-PC",
        "cpu_percent": 25.0,
        "ram_percent": -20.0,
        "disk_free_gb": 100.0,
        "uptime_seconds": 3600.0,
    }

    try:
        response = client.post(
            "/metrics",
            json=metric,
            headers={"X-API-Key": "test-key"},
        )

        assert response.status_code == 422

        errors = response.json()["detail"]

        assert any(
            "ram_percent" in error["loc"]
            for error in errors
        )

    finally:
        app.dependency_overrides.clear()

def test_get_latest_metrics():
    """Проверяет получение последних метрик компьютеров."""

    from unittest.mock import MagicMock
    from datetime import datetime, timezone

    from server.database import get_db

    fake_metric = MagicMock()
    fake_metric.id = 1
    fake_metric.hostname = "TEST-PC"
    fake_metric.cpu_percent = 25.0
    fake_metric.ram_percent = 50.0
    fake_metric.disk_free_gb = 100.0
    fake_metric.uptime_seconds = 3600.0
    fake_metric.timestamp = datetime.now(timezone.utc)

    fake_db = MagicMock()
    fake_db.scalars.return_value.all.return_value = [fake_metric]

    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        response = client.get("/metrics/latest")

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 1
        assert data[0]["hostname"] == "TEST-PC"
        assert data[0]["cpu_percent"] == 25.0

        fake_db.scalars.assert_called_once()

    finally:
        app.dependency_overrides.clear()

def test_get_metrics_history():
    """Проверяет получение истории метрик компьютера."""

    from unittest.mock import MagicMock
    from datetime import datetime, timezone

    from server.database import get_db

    fake_metric = MagicMock()
    fake_metric.id = 1
    fake_metric.hostname = "TEST-PC"
    fake_metric.cpu_percent = 25.0
    fake_metric.ram_percent = 50.0
    fake_metric.disk_free_gb = 100.0
    fake_metric.uptime_seconds = 3600.0
    fake_metric.timestamp = datetime.now(timezone.utc)

    fake_db = MagicMock()
    fake_db.scalars.return_value.all.return_value = [fake_metric]

    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        response = client.get(
            "/metrics/history",
            params={
                "hostname": "TEST-PC",
                "limit": 5,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 1
        assert data[0]["hostname"] == "TEST-PC"
        assert data[0]["cpu_percent"] == 25.0

        fake_db.scalars.assert_called_once()

    finally:
        app.dependency_overrides.clear()
