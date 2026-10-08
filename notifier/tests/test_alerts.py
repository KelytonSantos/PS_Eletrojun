from datetime import datetime, timedelta

from notifier.alerts import AlertEngine
from notifier.domain import SensorReading
from notifier.storage import AlertStorage


class FakeSender:
    def __init__(self):
        self.sent = []
        self.fail_for = set()

    def send_alert(self, recipient, alert_type, current_value, limit_value, measured_at_iso, source_topic):
        if recipient in self.fail_for:
            raise RuntimeError("smtp fail")
        self.sent.append(
            {
                "recipient": recipient,
                "alert_type": alert_type,
                "current_value": current_value,
                "limit_value": limit_value,
                "measured_at_iso": measured_at_iso,
                "source_topic": source_topic,
            }
        )


def test_alert_engine_cooldown_and_reset(tmp_path):
    storage = AlertStorage(str(tmp_path / "alerts.sqlite3"))
    storage.add_email("a@example.com")

    sender = FakeSender()
    engine = AlertEngine(storage=storage, sender=sender, cooldown_seconds=60)

    t0 = datetime(2026, 10, 5, 10, 0, 0)
    engine.process_reading(SensorReading(40.0, 10.0, t0), "esp32_Eletrojun_Dht11/sensor")
    assert len(sender.sent) == 2

    engine.process_reading(
        SensorReading(41.0, 9.0, t0 + timedelta(seconds=30)), "esp32_Eletrojun_Dht11/sensor"
    )
    assert len(sender.sent) == 2

    engine.process_reading(
        SensorReading(41.0, 9.0, t0 + timedelta(seconds=61)), "esp32_Eletrojun_Dht11/sensor"
    )
    assert len(sender.sent) == 4

    engine.process_reading(
        SensorReading(20.0, 80.0, t0 + timedelta(seconds=62)), "esp32_Eletrojun_Dht11/sensor"
    )
    engine.process_reading(
        SensorReading(40.0, 10.0, t0 + timedelta(seconds=63)), "esp32_Eletrojun_Dht11/sensor"
    )
    assert len(sender.sent) == 6


def test_alert_engine_partial_failure_does_not_block_others(tmp_path):
    storage = AlertStorage(str(tmp_path / "alerts.sqlite3"))
    storage.add_email("ok@example.com")
    storage.add_email("fail@example.com")

    sender = FakeSender()
    sender.fail_for.add("fail@example.com")

    engine = AlertEngine(storage=storage, sender=sender, cooldown_seconds=1)
    engine.process_reading(
        SensorReading(40.0, 10.0, datetime(2026, 10, 5, 10, 0, 0)), "esp32_Eletrojun_Dht11/sensor"
    )

    assert any(entry["recipient"] == "ok@example.com" for entry in sender.sent)
