from __future__ import annotations

import atexit
import logging
import os
from concurrent.futures import ThreadPoolExecutor

from .alerts import AlertEngine
from .config import Settings, load_settings
from .emailer import EmailSender
from .http_api import create_http_app
from .mqtt_consumer import MQTTConsumer
from .storage import AlertStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


class NotifierService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.storage = AlertStorage(settings.alert_db_path)
        self.sender = EmailSender(
            settings.smtp_host,
            settings.smtp_port,
            settings.smtp_username,
            settings.smtp_password,
            settings.smtp_from,
            settings.smtp_timeout_seconds,
            settings.smtp_security,
        )
        self.alert_engine = AlertEngine(
            storage=self.storage,
            sender=self.sender,
            cooldown_seconds=settings.alert_cooldown_seconds,
        )
        self.executor = ThreadPoolExecutor(max_workers=8)
        self.mqtt = MQTTConsumer(
            settings.mqtt_broker_url,
            settings.mqtt_port,
            settings.mqtt_sensor_topic,
            settings.mqtt_qos,
            settings.mqtt_client_id,
            settings.mqtt_username,
            settings.mqtt_password,
            self.executor,
            self.alert_engine,
        )
        self.http_app = create_http_app(self.storage)
        atexit.register(self.stop)

    def start(self) -> None:
        self.mqtt.start()

    def stop(self) -> None:
        try:
            self.mqtt.stop()
        except Exception:
            pass
        self.executor.shutdown(wait=False, cancel_futures=True)


def create_service(settings: Settings | None = None) -> NotifierService:
    return NotifierService(settings or load_settings())


_service: NotifierService | None = None


def get_service() -> NotifierService:
    global _service
    if _service is None:
        _service = create_service()
        _service.start()
    return _service


if os.getenv("SMTP_HOST"):
    try:
        service = get_service()
        http_app = service.http_app
    except Exception as exc:
        logging.getLogger(__name__).warning("Could not auto-start NotifierService: %s", exc)
        http_app = create_http_app(
            AlertStorage(os.getenv("ALERT_CONFIG_FILE", "notifier_data.sqlite3"))
        )
else:
    http_app = create_http_app(
        AlertStorage(os.getenv("ALERT_CONFIG_FILE", "notifier_data.sqlite3"))
    )


def main() -> None:
    svc = get_service()
    svc.http_app.run(host=svc._settings.http_host, port=svc._settings.http_port)


if __name__ == "__main__":
    main()
