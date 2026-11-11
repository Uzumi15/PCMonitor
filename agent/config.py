
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class AgentSettings(BaseSettings):
    """Настройки агента мониторинга."""

    server_url: str = "http://127.0.0.1:8000"
    api_key: str
    collect_interval: int = 30

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


agent_settings = AgentSettings()
