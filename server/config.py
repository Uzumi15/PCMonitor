
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Корневая папка проекта PCMonitor
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Настройки серверного приложения."""

    # Настройки FastAPI
    server_host: str = "127.0.0.1"
    server_port: int = 8000

    # Настройки PostgreSQL
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "pcmonitor"
    db_user: str = "postgres"
    db_password: str

    # API-ключ для проверки агентов
    api_key: str

    # Загрузка настроек из файла .env
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Единый объект настроек
settings = Settings()

