from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from .domain import SensorReading
from .storage import AlertStorage

logger = logging.getLogger(__name__)


@dataclass
class AlertState:
    active: bool = False
    last_sent_at: datetime | None = None


class AlertEngine:
    def __init__(self, storage: AlertStorage, sender, cooldown_seconds: int) -> None:
        self._storage = storage
        self._sender = sender
        self._cooldown = timedelta(seconds=max(0, cooldown_seconds))
        self._temp_state = AlertState()
        self._humi_state = AlertState()

    def process_reading(self, reading: SensorReading, source_topic: str) -> None:
        limits = self._storage.get_limits()

        temp_violated = reading.temperature >= limits.temp_max
        humi_violated = reading.humidity <= limits.humi_min

        self._handle_type(
            state=self._temp_state,
            violated=temp_violated,
            now=reading.measured_at,
            alert_type="temperatura",
            current_value=reading.temperature,
            limit_value=limits.temp_max,
            measured_at_iso=reading.measured_at.isoformat(),
            source_topic=source_topic,
        )
        self._handle_type(
            state=self._humi_state,
            violated=humi_violated,
            now=reading.measured_at,
            alert_type="umidade",
            current_value=reading.humidity,
            limit_value=limits.humi_min,
            measured_at_iso=reading.measured_at.isoformat(),
            source_topic=source_topic,
        )

    def _handle_type(
        self,
        state: AlertState,
        violated: bool,
        now: datetime,
        alert_type: str,
        current_value: float,
        limit_value: float,
        measured_at_iso: str,
        source_topic: str,
    ) -> None:
        if not violated:
            state.active = False
            state.last_sent_at = None
            return

        should_send = (not state.active) or (state.last_sent_at is None)
        if state.active and state.last_sent_at is not None:
            should_send = now - state.last_sent_at >= self._cooldown

        state.active = True
        if not should_send:
            return

        recipients = self._storage.list_emails()
        for recipient in recipients:
            try:
                self._sender.send_alert(
                    recipient=recipient,
                    alert_type=alert_type,
                    current_value=current_value,
                    limit_value=limit_value,
                    measured_at_iso=measured_at_iso,
                    source_topic=source_topic,
                )
                logger.info("Alert sent", extra={"alert_type": alert_type, "recipient": recipient})
            except Exception as exc:  # pragma: no cover - defensive path
                logger.error(
                    "Alert delivery failed",
                    extra={"alert_type": alert_type, "recipient": recipient, "error": str(exc)},
                )
        state.last_sent_at = now
