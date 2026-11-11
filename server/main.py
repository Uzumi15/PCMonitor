
import logging

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from server.database import get_db
from server.models import SystemMetric
from server.schemas import MetricCreate, MetricResponse
from server.security import verify_api_key

from pathlib import Path

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

from fastapi.staticfiles import StaticFiles

# Настраиваем журналирование ошибок
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Создаём приложение FastAPI

# Создаём приложение FastAPI
app = FastAPI(
    title="PCMonitor API",
    description="Сервер мониторинга компьютеров",
    version="1.0.0",
)

# Путь к папке server
BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

# Подключаем HTML-шаблоны
templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)

@app.get("/health")
def health_check():
    """Проверяет, что HTTP-сервер работает."""
    return {"status": "ok"}


@app.post(
    "/metrics",
    response_model=MetricResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_metric(
    metric: MetricCreate,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Принимает и сохраняет метрики компьютера."""

    new_metric = SystemMetric(
        hostname=metric.hostname,
        cpu_percent=metric.cpu_percent,
        ram_percent=metric.ram_percent,
        disk_free_gb=metric.disk_free_gb,
        uptime_seconds=metric.uptime_seconds,
    )

    try:
        db.add(new_metric)
        db.commit()
        db.refresh(new_metric)

    except SQLAlchemyError:
        db.rollback()

        logger.exception(
            "Database error while saving metrics"
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable",
        )

    return new_metric

@app.get("/metrics/latest", response_model=list[MetricResponse])
def get_latest_metrics(
    db: Session = Depends(get_db),
):
    """Возвращает последнюю метрику каждого компьютера."""

    latest_ids = (
        select(func.max(SystemMetric.id))
        .group_by(SystemMetric.hostname)
    )

    query = (
        select(SystemMetric)
        .where(SystemMetric.id.in_(latest_ids))
        .order_by(SystemMetric.hostname)
    )

    try:
        metrics = db.scalars(query).all()
        return metrics

    except SQLAlchemyError:
        logger.exception("Database error while reading metrics")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable",
        )


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    """Открывает веб-панель мониторинга."""

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={},
    )

@app.get("/metrics/history", response_model=list[MetricResponse])
def get_metrics_history(
    hostname: str = Query(min_length=1, max_length=255),
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Возвращает историю метрик выбранного компьютера."""

    query = (
        select(SystemMetric)
        .where(SystemMetric.hostname == hostname)
        .order_by(
            SystemMetric.timestamp.desc(),
            SystemMetric.id.desc()
        )
        .limit(limit)
    )

    try:
        metrics = db.scalars(query).all()
        return list(reversed(metrics))

    except SQLAlchemyError:
        logger.exception("Database error while reading metric history")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable",
        )
