import pytest

from notifier.config import load_settings


@pytest.fixture(autouse=True)
def required_env(monkeypatch, tmp_path):
    monkeypatch.setenv("SMTP_HOST", "localhost")
    monkeypatch.setenv("SMTP_FROM", "from@example.com")
    monkeypatch.setenv("ALERT_CONFIG_FILE", str(tmp_path / "alerts.sqlite3"))


def test_load_settings_defaults():
    settings = load_settings()
    assert settings.smtp_security == "none"
    assert settings.mqtt_sensor_topic == "esp32_Eletrojun_Dht11/sensor"


@pytest.mark.parametrize(
    "name,value,expected",
    [
        ("MQTT_PORT", "abc", "MQTT_PORT"),
        ("SMTP_PORT", "0", "SMTP_PORT"),
        ("MQTT_QOS", "3", "MQTT_QOS"),
        ("ALERT_COOLDOWN_SECONDS", "-1", "ALERT_COOLDOWN_SECONDS"),
        ("SMTP_TIMEOUT_SECONDS", "0", "SMTP_TIMEOUT_SECONDS"),
        ("HTTP_PORT", "70000", "HTTP_PORT"),
        ("SMTP_SECURITY", "ssl", "SMTP_SECURITY"),
    ],
)
def test_load_settings_invalid_values_show_clear_message(monkeypatch, name, value, expected):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError) as exc:
        load_settings()
    assert expected in str(exc.value)


def test_load_settings_valid_security(monkeypatch):
    monkeypatch.setenv("SMTP_SECURITY", "starttls")
    settings = load_settings()
    assert settings.smtp_security == "starttls"
