
import json
import sqlite3
from pathlib import Path


BUFFER_PATH = Path(__file__).resolve().parent / "buffer.db"


def init_buffer() -> None:
    """Создаёт таблицу для неотправленных метрик."""

    with sqlite3.connect(BUFFER_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pending_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL
            )
        """)


def save_metric(metric: dict) -> None:
    """Сохраняет метрику в локальный буфер."""

    with sqlite3.connect(BUFFER_PATH) as conn:
        conn.execute(
            "INSERT INTO pending_metrics (data) VALUES (?)",
            (json.dumps(metric),),
        )


def get_pending_metrics() -> list[tuple[int, dict]]:
    """Возвращает все неотправленные метрики."""

    with sqlite3.connect(BUFFER_PATH) as conn:
        rows = conn.execute(
            "SELECT id, data FROM pending_metrics ORDER BY id"
        ).fetchall()

    return [
        (row_id, json.loads(data))
        for row_id, data in rows
    ]


def delete_metric(metric_id: int) -> None:
    """Удаляет метрику после успешной отправки."""

    with sqlite3.connect(BUFFER_PATH) as conn:
        conn.execute(
            "DELETE FROM pending_metrics WHERE id = ?",
            (metric_id,),
        )
