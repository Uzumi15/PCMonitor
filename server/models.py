
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Identity, Index, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый класс для моделей базы данных."""
    pass


class SystemMetric(Base):
    """Модель таблицы system_metrics."""

    __tablename__ = "system_metrics"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )

    hostname: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    cpu_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    ram_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    disk_free_gb: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    uptime_seconds: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "idx_metrics_hostname_timestamp",
            "hostname",
            timestamp.desc(),
        ),
    )