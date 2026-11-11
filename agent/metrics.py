
import os
import socket
import time
from pathlib import Path

import psutil


def collect_metrics() -> dict:
    """Собирает основные метрики компьютера."""

    hostname = socket.gethostname()

    cpu_percent = psutil.cpu_percent(interval=1)

    ram_percent = psutil.virtual_memory().percent

    system_drive = Path(os.environ.get("SystemDrive", "C:") + "\\")

    disk_free_bytes = psutil.disk_usage(
        str(system_drive)
    ).free

    disk_free_gb = round(
        disk_free_bytes / (1024 ** 3), 2
    )

    uptime_seconds = max(
        0.0,
        time.time() - psutil.boot_time()
    )

    return {
        "hostname": hostname,
        "cpu_percent": float(cpu_percent),
        "ram_percent": float(ram_percent),
        "disk_free_gb": disk_free_gb,
        "uptime_seconds": round(uptime_seconds, 2),
    }
