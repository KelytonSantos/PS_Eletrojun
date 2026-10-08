from __future__ import annotations

import smtplib
from email.message import EmailMessage


class EmailSender:
    def __init__(
        self,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        sender: str,
        timeout_seconds: float,
        security: str = "none",
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._sender = sender
        self._timeout_seconds = timeout_seconds
        self._security = security

    def send_alert(
        self,
        recipient: str,
        alert_type: str,
        current_value: float,
        limit_value: float,
        measured_at_iso: str,
        source_topic: str,
    ) -> None:
        subject = f"[ALERTA] {alert_type} fora do limite"
        text = (
            f"Tipo: {alert_type}\n"
            f"Valor atual: {current_value}\n"
            f"Limite: {limit_value}\n"
            f"Data/Hora: {measured_at_iso}\n"
            f"Origem MQTT: {source_topic}\n"
        )
        html = (
            "<html><body>"
            f"<h2>Alerta de {alert_type}</h2>"
            f"<p><strong>Valor atual:</strong> {current_value}</p>"
            f"<p><strong>Limite:</strong> {limit_value}</p>"
            f"<p><strong>Data/Hora:</strong> {measured_at_iso}</p>"
            f"<p><strong>Origem MQTT:</strong> {source_topic}</p>"
            "</body></html>"
        )

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self._sender
        message["To"] = recipient
        message.set_content(text)
        message.add_alternative(html, subtype="html")

        smtp_factory = smtplib.SMTP_SSL if self._security == "tls" else smtplib.SMTP
        with smtp_factory(self._host, self._port, timeout=self._timeout_seconds) as smtp:
            smtp.ehlo()
            if self._security == "starttls":
                smtp.starttls()
                smtp.ehlo()
            if self._username:
                smtp.login(self._username, self._password or "")
            smtp.send_message(message)
