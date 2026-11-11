
import logging

import requests


logger = logging.getLogger(__name__)


def send_metrics(
    metrics: dict,
    server_url: str,
    api_key: str,
) -> bool:
    """Отправляет метрики серверу и возвращает результат."""

    url = f"{server_url.rstrip('/')}/metrics"

    headers = {
        "X-API-Key": api_key,
    }

    try:
        response = requests.post(
            url,
            json=metrics,
            headers=headers,
            timeout=10,
        )

        response.raise_for_status()

        logger.info(
            "Metrics sent successfully: %s",
            metrics["hostname"],
        )

        return True

    except requests.exceptions.RequestException as error:
        logger.warning(
            "Failed to send metrics: %s",
            error,
        )

        return False
