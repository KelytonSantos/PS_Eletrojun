from types import SimpleNamespace

from notifier.alerts import AlertEngine
from notifier.mqtt_consumer import MQTTConsumer
from notifier.storage import AlertStorage


class InlineExecutor:
    def submit(self, fn):
        fn()


class FakeClient:
    def __init__(self, *args, **kwargs):
        self.on_connect = None
        self.on_message = None
        self.on_disconnect = None

    def username_pw_set(self, username, password):
        return None


class FakeSMTPSender:
    def __init__(self):
        self.calls = []

    def send_alert(self, recipient, alert_type, current_value, limit_value, measured_at_iso, source_topic):
        self.calls.append(
            {
                "recipient": recipient,
                "alert_type": alert_type,
                "current_value": current_value,
                "limit_value": limit_value,
                "measured_at_iso": measured_at_iso,
                "source_topic": source_topic,
            }
        )


def test_integration_mqtt_to_alerts_with_fake_broker_and_smtp(tmp_path):
    storage = AlertStorage(str(tmp_path / "alerts.sqlite3"))
    storage.add_email("dest@example.com")

    sender = FakeSMTPSender()
    engine = AlertEngine(storage=storage, sender=sender, cooldown_seconds=0)
    consumer = MQTTConsumer(
        "localhost",
        1883,
        "esp32_Eletrojun_Dht11/sensor",
        1,
        "notifier",
        None,
        None,
        InlineExecutor(),
        engine,
        mqtt_client_factory=FakeClient,
    )

    msg = SimpleNamespace(
        payload=b"40.0,10.0,2026-10-05T20:34:38", topic="esp32_Eletrojun_Dht11/sensor"
    )
    consumer._on_message(consumer.client, None, msg)

    alert_types = {item["alert_type"] for item in sender.calls}
    assert alert_types == {"temperatura", "umidade"}
    assert all(item["recipient"] == "dest@example.com" for item in sender.calls)
