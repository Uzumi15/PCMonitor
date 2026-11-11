
import logging
import time

from agent.buffer import (
    init_buffer,
    save_metric,
    get_pending_metrics,
    delete_metric,
)
from agent.config import agent_settings
from agent.metrics import collect_metrics
from agent.sender import send_metrics


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def process_metrics() -> None:
    """Собирает и отправляет текущие показатели."""

    metric = collect_metrics()

    logger.info(
        "Collected metrics from %s",
        metric["hostname"],
    )

    success = send_metrics(
        metrics=metric,
        server_url=agent_settings.server_url,
        api_key=agent_settings.api_key,
    )

    if not success:
        save_metric(metric)
        logger.warning("Metric saved to SQLite buffer")


def retry_pending_metrics() -> None:
    """Повторно отправляет накопленные метрики."""

    pending = get_pending_metrics()

    for metric_id, metric in pending:
        success = send_metrics(
            metrics=metric,
            server_url=agent_settings.server_url,
            api_key=agent_settings.api_key,
        )

        if success:
            delete_metric(metric_id)
            logger.info(
                "Buffered metric %s sent successfully",
                metric_id,
            )
        else:
            logger.warning(
                "Could not send buffered metric %s",
                metric_id,
            )
            break

def main() -> None:
    """Запускает постоянный мониторинг компьютера."""

    init_buffer()

    logger.info("PCMonitor agent started")

    try:
        while True:
            try:
                retry_pending_metrics()
                process_metrics()

            except Exception:
                logger.exception("Agent iteration failed")

            time.sleep(agent_settings.collect_interval)

    except KeyboardInterrupt:
        logger.info("PCMonitor agent stopped by user")


if __name__ == "__main__":
    main()
