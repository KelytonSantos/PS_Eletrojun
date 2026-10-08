from __future__ import annotations

import logging
import uuid
from concurrent.futures import Executor

import paho.mqtt.client as mqtt

from .domain import parse_sensor_payload

logger = logging.getLogger(__name__)


class MQTTConsumer:
    def __init__(
        self,
        broker_url: str,
        port: int,
        topic: str,
        qos: int,
        client_id_base: str,
        username: str | None,
        password: str | None,
        executor: Executor,
        alert_engine,
        mqtt_client_factory=mqtt.Client,
    ) -> None:
        self._broker_url = broker_url
        self._port = port
        self._topic = topic
        self._qos = qos
        self._executor = executor
        self._alert_engine = alert_engine

        unique_id = f"{client_id_base}-{uuid.uuid4().hex[:8]}"
        self._client = mqtt_client_factory(mqtt.CallbackAPIVersion.VERSION2, client_id=unique_id)
        if username:
            self._client.username_pw_set(username, password)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

    @property
    def client(self):
        return self._client

    def start(self) -> None:
        self._client.reconnect_delay_set(min_delay=1, max_delay=30)
        try:
            self._client.connect(self._broker_url, self._port)
        except Exception as exc:
            logger.error("MQTT initial connection failed; retrying asynchronously", extra={"error": str(exc)})
            self._client.connect_async(self._broker_url, self._port)
        self._client.loop_start()

    def stop(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            client.subscribe(self._topic, qos=self._qos)
            logger.info("MQTT connected and subscribed", extra={"topic": self._topic})
            return
        logger.error("MQTT connection failed", extra={"reason_code": reason_code})

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        logger.warning("MQTT disconnected", extra={"reason_code": reason_code})
        if reason_code != 0:
            try:
                client.reconnect()
            except Exception as exc:
                logger.error("MQTT reconnect attempt failed", extra={"error": str(exc)})

    def _on_message(self, client, userdata, message):
        try:
            payload = message.payload.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            logger.warning("Payload is not valid UTF-8", extra={"error": str(exc)})
            return

        topic = message.topic

        def _process() -> None:
            try:
                reading = parse_sensor_payload(payload)
            except ValueError as exc:
                logger.warning(
                    "Invalid sensor payload ignored", extra={"topic": topic, "error": str(exc)}
                )
                return
            self._alert_engine.process_reading(reading, source_topic=topic)

        self._executor.submit(_process)
