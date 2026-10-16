import smtplib

from notifier.emailer import EmailSender


class FakeSMTP:
    instances = []

    def __init__(self, host, port, timeout):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.logged_in = None
        self.sent_messages = []
        self.ehlo_calls = 0
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def ehlo(self):
        self.ehlo_calls += 1

    def starttls(self):
        self.started_tls = True

    def login(self, username, secret):
        self.logged_in = (username, secret)

    def send_message(self, message):
        self.sent_messages.append(message)


def test_email_sender_builds_message_timeout_and_auth(monkeypatch):
    FakeSMTP.instances.clear()
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

    sender = EmailSender("smtp.local", 2525, "user", "pw", "no-reply@example.com", 7.5)

    sender.send_alert(
        recipient="dest@example.com",
        alert_type="temperatura",
        current_value=40.0,
        limit_value=35.0,
        measured_at_iso="2026-10-05T20:34:38",
        source_topic="esp32_Eletrojun_Dht11/sensor",
    )

    smtp = FakeSMTP.instances[0]
    assert smtp.host == "smtp.local"
    assert smtp.port == 2525
    assert smtp.timeout == 7.5
    assert smtp.logged_in == ("user", "pw")

    message = smtp.sent_messages[0]
    assert message["Subject"] == "[ALERTA] temperatura fora do limite"
    assert message["To"] == "dest@example.com"
    assert message["From"] == "no-reply@example.com"

    parts = message.get_payload()
    assert len(parts) == 2
    assert "Tipo: temperatura" in parts[0].get_payload()
    assert "Origem MQTT: esp32_Eletrojun_Dht11/sensor" in parts[0].get_payload()
    assert "ELETRONJUN" in parts[0].get_payload()
    assert "<h2>Alerta de temperatura</h2>" in parts[1].get_payload()
    assert "EletronJun" in parts[1].get_payload()


def test_email_sender_uses_starttls_when_configured(monkeypatch):
    FakeSMTP.instances.clear()
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

    sender = EmailSender(
        "smtp.local", 587, None, None, "no-reply@example.com", 10, security="starttls"
    )

    sender.send_alert(
        recipient="dest@example.com",
        alert_type="umidade",
        current_value=10.0,
        limit_value=20.0,
        measured_at_iso="2026-10-05T20:34:38",
        source_topic="esp32_Eletrojun_Dht11/sensor",
    )

    smtp = FakeSMTP.instances[0]
    assert smtp.started_tls is True
    assert smtp.ehlo_calls >= 2


def test_email_sender_uses_tls_socket_when_configured(monkeypatch):
    FakeSMTP.instances.clear()
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)

    sender = EmailSender("smtp.local", 465, None, None, "no-reply@example.com", 10, security="tls")

    sender.send_alert(
        recipient="dest@example.com",
        alert_type="umidade",
        current_value=10.0,
        limit_value=20.0,
        measured_at_iso="2026-10-05T20:34:38",
        source_topic="esp32_Eletrojun_Dht11/sensor",
    )

    assert FakeSMTP.instances[0].port == 465


def test_email_sender_units_excess_and_html_escaping(monkeypatch):
    FakeSMTP.instances.clear()
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

    sender = EmailSender("smtp.local", 2525, None, None, "no-reply@example.com", 10)

    # 1. Validação de unidade exibida, cálculo de excesso e horário Brasília
    sender.send_alert(
        recipient="dest@example.com",
        alert_type="temperatura",
        current_value=40.0,
        limit_value=35.0,
        measured_at_iso="2026-10-13T13:30:00",
        source_topic="esp32_Eletrojun_Dht11/sensor",
    )

    smtp = FakeSMTP.instances[0]
    message = smtp.sent_messages[0]
    parts = message.get_payload()
    html_payload = parts[1].get_content()

    # Unidade exibida no valor medido e no limite
    assert "40.0 °C" in html_payload
    assert "35.0 °C" in html_payload

    # Cálculo do excesso (5.0 °C acima do limite (+14.3%))
    assert "▲ 5.0 °C acima do limite (+14.3%)" in html_payload

    # Horário formatado no padrão Brasília
    assert "13/10/2026 às 13:30 (Brasília)" in html_payload

    # 2. Validação de escape de HTML contra XSS/HTML Injection
    sender.send_alert(
        recipient="dest@example.com",
        alert_type="<b>x</b>",
        current_value=50.0,
        limit_value=40.0,
        measured_at_iso="2026-10-13T13:30:00<script>",
        source_topic="topic/<script>alert(1)</script>",
    )

    smtp2 = FakeSMTP.instances[1]
    message_xss = smtp2.sent_messages[0]
    html_xss = message_xss.get_payload()[1].get_content()

    assert "<b>x</b>" not in html_xss
    assert "&lt;b&gt;x&lt;/b&gt;" in html_xss
    assert "<script>" not in html_xss
    assert "&lt;script&gt;" in html_xss
    assert "topic/<script>alert(1)</script>" not in html_xss
    assert "topic/&lt;script&gt;alert(1)&lt;/script&gt;" in html_xss

