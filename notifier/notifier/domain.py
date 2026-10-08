from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime

EMAIL_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$")

TEMP_MIN = -50.0
TEMP_MAX = 120.0
HUMI_MIN = 0.0
HUMI_MAX = 100.0


@dataclass(frozen=True)
class SensorReading:
    temperature: float
    humidity: float
    measured_at: datetime


@dataclass(frozen=True)
class Limits:
    temp_max: float
    humi_min: float


def parse_sensor_payload(payload: str) -> SensorReading:
    text = (payload or "").strip()
    if not text:
        raise ValueError("Empty payload")

    parts = [part.strip() for part in text.split(",")]
    if len(parts) < 3:
        raise ValueError("Payload must have at least 3 fields")

    try:
        temperature = float(parts[0])
        humidity = float(parts[1])
    except ValueError as exc:
        raise ValueError("Temperature and humidity must be decimals") from exc

    if not math.isfinite(temperature) or not math.isfinite(humidity):
        raise ValueError("Temperature and humidity must be finite values")

    try:
        measured_at = datetime.fromisoformat(parts[2])
    except ValueError as exc:
        raise ValueError("Invalid datetime format") from exc

    return SensorReading(temperature=temperature, humidity=humidity, measured_at=measured_at)


def normalize_email(email: str) -> tuple[str, str]:
    normalized = (email or "").strip()
    if not normalized:
        raise ValueError("Email cannot be empty")
    if not EMAIL_RE.match(normalized):
        raise ValueError("Email format is invalid")
    return normalized, normalized.lower()


def validate_limits(temp: object, humi: object) -> Limits:
    try:
        temp_value = float(temp)
        humi_value = float(humi)
    except (TypeError, ValueError) as exc:
        raise ValueError("temp and humi must be numbers") from exc

    if not math.isfinite(temp_value) or not math.isfinite(humi_value):
        raise ValueError("temp and humi must be finite values")

    if not (TEMP_MIN <= temp_value <= TEMP_MAX):
        raise ValueError("temp out of range (-50 to 120)")
    if not (HUMI_MIN <= humi_value <= HUMI_MAX):
        raise ValueError("humi out of range (0 to 100)")

    return Limits(temp_max=temp_value, humi_min=humi_value)
