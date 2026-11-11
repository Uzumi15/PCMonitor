
from sqlalchemy import inspect

from server.models import SystemMetric

from sqlalchemy import inspect as inspect_database

from server.database import engine

from sqlalchemy import BigInteger, DateTime, Float, String

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

def test_system_metric_table_structure():
    """Проверяет структуру таблицы system_metrics."""

    table = inspect(SystemMetric).local_table

    assert table.name == "system_metrics"

    required_columns = {
        "id",
        "hostname",
        "cpu_percent",
        "ram_percent",
        "disk_free_gb",
        "uptime_seconds",
        "timestamp",
    }

    actual_columns = set(table.columns.keys())

    assert required_columns.issubset(actual_columns)

    assert table.primary_key.columns.keys() == ["id"]

def test_postgresql_table_exists():
    """Проверяет наличие таблицы в PostgreSQL."""

    inspector = inspect_database(engine)

    tables = inspector.get_table_names()

    assert "system_metrics" in tables

def test_postgresql_columns_match_model():
    """Проверяет соответствие столбцов PostgreSQL и SQLAlchemy."""

    inspector = inspect_database(engine)

    database_columns = {
        column["name"]
        for column in inspector.get_columns("system_metrics")
    }

    model_columns = set(
        SystemMetric.__table__.columns.keys()
    )

    assert database_columns == model_columns

def test_postgresql_column_types():
    """Проверяет типы данных столбцов PostgreSQL."""

    inspector = inspect_database(engine)

    columns = {
        column["name"]: column
        for column in inspector.get_columns("system_metrics")
    }

    assert isinstance(columns["id"]["type"], BigInteger)

    assert isinstance(columns["hostname"]["type"], String)

    assert isinstance(columns["cpu_percent"]["type"], Float)
    assert isinstance(columns["ram_percent"]["type"], Float)
    assert isinstance(columns["disk_free_gb"]["type"], Float)
    assert isinstance(columns["uptime_seconds"]["type"], Float)

    timestamp_type = columns["timestamp"]["type"]

    assert isinstance(timestamp_type, DateTime)
    assert timestamp_type.timezone is True

def test_postgresql_not_null_constraints():
    """Проверяет обязательность столбцов PostgreSQL."""

    inspector = inspect_database(engine)

    columns = {
        column["name"]: column
        for column in inspector.get_columns("system_metrics")
    }

    required_columns = {
        "id",
        "hostname",
        "cpu_percent",
        "ram_percent",
        "disk_free_gb",
        "uptime_seconds",
        "timestamp",
    }

    for column_name in required_columns:
        assert columns[column_name]["nullable"] is False

def test_postgresql_check_constraints():
    """Проверяет наличие CHECK-ограничений PostgreSQL."""

    inspector = inspect_database(engine)

    constraints = inspector.get_check_constraints(
        "system_metrics"
    )

    assert len(constraints) >= 4

    for constraint in constraints:
        assert constraint["sqltext"]

def test_postgresql_rejects_invalid_cpu():
    """Проверяет, что PostgreSQL отклоняет CPU выше 100%."""

    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            with pytest.raises(IntegrityError):
                connection.execute(
                    text("""
                        INSERT INTO system_metrics (
                            hostname,
                            cpu_percent,
                            ram_percent,
                            disk_free_gb,
                            uptime_seconds
                        )
                        VALUES (
                            :hostname,
                            :cpu,
                            :ram,
                            :disk,
                            :uptime
                        )
                    """),
                    {
                        "hostname": "PYTEST-PC",
                        "cpu": 150.0,
                        "ram": 50.0,
                        "disk": 100.0,
                        "uptime": 3600.0,
                    },
                )

        finally:
            transaction.rollback()

def test_postgresql_insert_valid_metric():
    """Проверяет сохранение и чтение корректной метрики."""

    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            result = connection.execute(
                text("""
                    INSERT INTO system_metrics (
                        hostname,
                        cpu_percent,
                        ram_percent,
                        disk_free_gb,
                        uptime_seconds
                    )
                    VALUES (
                        :hostname,
                        :cpu,
                        :ram,
                        :disk,
                        :uptime
                    )
                    RETURNING id
                """),
                {
                    "hostname": "PYTEST-PC",
                    "cpu": 25.0,
                    "ram": 50.0,
                    "disk": 100.0,
                    "uptime": 3600.0,
                },
            )

            metric_id = result.scalar_one()

            saved_metric = connection.execute(
                text("""
                    SELECT
                        hostname,
                        cpu_percent,
                        ram_percent,
                        disk_free_gb,
                        uptime_seconds
                    FROM system_metrics
                    WHERE id = :metric_id
                """),
                {"metric_id": metric_id},
            ).mappings().one()

            assert saved_metric["hostname"] == "PYTEST-PC"
            assert saved_metric["cpu_percent"] == 25.0
            assert saved_metric["ram_percent"] == 50.0
            assert saved_metric["disk_free_gb"] == 100.0
            assert saved_metric["uptime_seconds"] == 3600.0

        finally:
            transaction.rollback()
