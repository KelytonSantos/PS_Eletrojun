from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    mqtt_broker_url: str
    mqtt_port: int
    mqtt_username: str | None
    mqtt_password: str | None
    mqtt_sensor_topic: str
    mqtt_client_id: str
    mqtt_qos: int
    smtp_host: str
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    smtp_from: str
    alert_db_path: str
    alert_cooldown_seconds: int
    smtp_timeout_seconds: float
    http_host: str
    http_port: int


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Environment variable '{name}' is required")
    return value


def _optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def _parse_db_path() -> str:
    database_url = _optional_env("ALERT_DATABASE_URL")
    if database_url:
        if database_url.startswith("sqlite:///"):
            return database_url.removeprefix("sqlite:///")
        raise ValueError("ALERT_DATABASE_URL must use sqlite:///path format")

    config_file = _optional_env("ALERT_CONFIG_FILE")
    if config_file:
        return config_file

    return "notifier_data.sqlite3"


def load_settings() -> Settings:
    return Settings(
        mqtt_broker_url=os.getenv("MQTT_BROKER_URL", "localhost").strip() or "localhost",
        mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
        mqtt_username=_optional_env("MQTT_USERNAME"),
        mqtt_password=_optional_env("MQTT_PASSWORD"),
        mqtt_sensor_topic=os.getenv("MQTT_SENSOR_TOPIC", "esp32_Eletrojun_Dht11/sensor").strip()
        or "esp32_Eletrojun_Dht11/sensor",
        mqtt_client_id=os.getenv("MQTT_CLIENT_ID", "notifier").strip() or "notifier",
        mqtt_qos=int(os.getenv("MQTT_QOS", "1")),
        smtp_host=_require_env("SMTP_HOST"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=_optional_env("SMTP_USERNAME"),
        smtp_password=_optional_env("SMTP_PASSWORD"),
        smtp_from=_require_env("SMTP_FROM"),
        alert_db_path=_parse_db_path(),
        alert_cooldown_seconds=int(os.getenv("ALERT_COOLDOWN_SECONDS", "300")),
        smtp_timeout_seconds=float(os.getenv("SMTP_TIMEOUT_SECONDS", "10")),
        http_host=os.getenv("HTTP_HOST", "0.0.0.0"),
        http_port=int(os.getenv("HTTP_PORT", "8080")),
    )
