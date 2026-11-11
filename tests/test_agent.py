
from agent.metrics import collect_metrics

from unittest.mock import patch

from agent.sender import send_metrics

import requests

from agent import buffer

from agent import main as agent_main

def test_collect_metrics_returns_dict():
    """Проверяет, что агент возвращает словарь."""

    metrics = collect_metrics()

    assert isinstance(metrics, dict)


def test_collect_metrics_has_required_fields():
    """Проверяет наличие обязательных полей."""

    metrics = collect_metrics()

    required_fields = {
        "hostname",
        "cpu_percent",
        "ram_percent",
        "disk_free_gb",
        "uptime_seconds",
    }

    assert required_fields.issubset(metrics.keys())



def test_collect_metrics_values():
    """Проверяет типы и допустимые значения метрик."""

    metrics = collect_metrics()

    assert isinstance(metrics["hostname"], str)
    assert len(metrics["hostname"]) > 0

    assert 0 <= metrics["cpu_percent"] <= 100
    assert 0 <= metrics["ram_percent"] <= 100

    assert metrics["disk_free_gb"] >= 0
    assert metrics["uptime_seconds"] >= 0

def test_send_metrics_success():
    """Проверяет успешную отправку без настоящего сервера."""

    metric = {
        "hostname": "TEST-PC",
        "cpu_percent": 25.0,
        "ram_percent": 50.0,
        "disk_free_gb": 100.0,
        "uptime_seconds": 3600.0,
    }

    with patch("agent.sender.requests.post") as mock_post:
        mock_post.return_value.status_code = 201

        result = send_metrics(
            metrics=metric,
            server_url="http://127.0.0.1:8000",
            api_key="test-key",
        )

        assert result is True

        mock_post.assert_called_once_with(
            "http://127.0.0.1:8000/metrics",
            json=metric,
            headers={"X-API-Key": "test-key"},
            timeout=10,
        )

def test_send_metrics_connection_error():
    """Проверяет обработку ошибки соединения."""

    metric = {
        "hostname": "TEST-PC",
        "cpu_percent": 25.0,
        "ram_percent": 50.0,
        "disk_free_gb": 100.0,
        "uptime_seconds": 3600.0,
    }

    with patch("agent.sender.requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.ConnectionError(
            "Server unavailable"
        )

        result = send_metrics(
            metrics=metric,
            server_url="http://127.0.0.1:8000",
            api_key="test-key",
        )

        assert result is False
        mock_post.assert_called_once()

def test_buffer_save_and_read(tmp_path, monkeypatch):
    """Проверяет сохранение и чтение метрик в SQLite."""

    test_db = tmp_path / "test_buffer.db"

    monkeypatch.setattr(
        buffer,
        "BUFFER_PATH",
        test_db,
    )

    buffer.init_buffer()

    metric = {
        "hostname": "TEST-PC",
        "cpu_percent": 25.0,
        "ram_percent": 50.0,
        "disk_free_gb": 100.0,
        "uptime_seconds": 3600.0,
    }

    buffer.save_metric(metric)

    pending = buffer.get_pending_metrics()

    assert len(pending) == 1

    metric_id, saved_metric = pending[0]

    assert metric_id > 0
    assert saved_metric == metric



def test_buffer_delete_metric(tmp_path, monkeypatch):
    """Проверяет удаление только выбранной метрики."""

    test_db = tmp_path / "test_buffer.db"

    monkeypatch.setattr(
        buffer,
        "BUFFER_PATH",
        test_db,
    )

    buffer.init_buffer()

    first_metric = {
        "hostname": "PC-01",
        "cpu_percent": 20.0,
    }

    second_metric = {
        "hostname": "PC-02",
        "cpu_percent": 40.0,
    }

    buffer.save_metric(first_metric)
    buffer.save_metric(second_metric)

    pending = buffer.get_pending_metrics()

    assert len(pending) == 2

    first_id = pending[0][0]

    buffer.delete_metric(first_id)

    remaining = buffer.get_pending_metrics()

    assert len(remaining) == 1
    assert remaining[0][1] == second_metric

def test_process_metrics_saves_on_failure(tmp_path, monkeypatch):
    """Проверяет сохранение метрики при ошибке отправки."""

    test_db = tmp_path / "test_buffer.db"

    monkeypatch.setattr(
        buffer,
        "BUFFER_PATH",
        test_db,
    )

    buffer.init_buffer()

    test_metric = {
        "hostname": "TEST-PC",
        "cpu_percent": 25.0,
        "ram_percent": 50.0,
        "disk_free_gb": 100.0,
        "uptime_seconds": 3600.0,
    }

    with (
        patch(
            "agent.main.collect_metrics",
            return_value=test_metric,
        ) as mock_collect,
        patch(
            "agent.main.send_metrics",
            return_value=False,
        ) as mock_send,
    ):
        agent_main.process_metrics()

        mock_collect.assert_called_once()
        mock_send.assert_called_once()

    pending = buffer.get_pending_metrics()

    assert len(pending) == 1
    assert pending[0][1] == test_metric


def test_retry_pending_metrics_success(tmp_path, monkeypatch):
    """Проверяет повторную отправку и очистку SQLite."""

    test_db = tmp_path / "test_buffer.db"

    monkeypatch.setattr(
        buffer,
        "BUFFER_PATH",
        test_db,
    )

    buffer.init_buffer()

    test_metric = {
        "hostname": "TEST-PC",
        "cpu_percent": 25.0,
        "ram_percent": 50.0,
        "disk_free_gb": 100.0,
        "uptime_seconds": 3600.0,
    }

    buffer.save_metric(test_metric)

    assert len(buffer.get_pending_metrics()) == 1

    with patch(
        "agent.main.send_metrics",
        return_value=True,
    ) as mock_send:

        agent_main.retry_pending_metrics()

        mock_send.assert_called_once_with(
            metrics=test_metric,
            server_url=agent_main.agent_settings.server_url,
            api_key=agent_main.agent_settings.api_key,
        )

    assert len(buffer.get_pending_metrics()) == 0


def test_retry_pending_metrics_failure(tmp_path, monkeypatch):
    """Проверяет сохранение метрик при повторной ошибке."""

    test_db = tmp_path / "test_buffer.db"

    monkeypatch.setattr(
        buffer,
        "BUFFER_PATH",
        test_db,
    )

    buffer.init_buffer()

    first_metric = {
        "hostname": "PC-01",
        "cpu_percent": 20.0,
    }

    second_metric = {
        "hostname": "PC-02",
        "cpu_percent": 40.0,
    }

    buffer.save_metric(first_metric)
    buffer.save_metric(second_metric)

    with patch(
        "agent.main.send_metrics",
        return_value=False,
    ) as mock_send:

        agent_main.retry_pending_metrics()

        mock_send.assert_called_once()

    pending = buffer.get_pending_metrics()

    assert len(pending) == 2
    assert pending[0][1] == first_metric
    assert pending[1][1] == second_metric
