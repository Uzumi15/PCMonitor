
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MetricCreate(BaseModel):
    """Данные, которые агент отправляет серверу."""

    model_config = ConfigDict(extra="forbid", strict=True)

    hostname: str = Field(
        min_length=1,
        max_length=255,
    )

    cpu_percent: float = Field(ge=0, le=100)
    ram_percent: float = Field(ge=0, le=100)
    disk_free_gb: float = Field(ge=0)
    uptime_seconds: float = Field(ge=0)


class MetricResponse(MetricCreate):
    """Данные метрики, возвращаемые сервером."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
