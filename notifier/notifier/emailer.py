from __future__ import annotations

import html
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

try:
    from zoneinfo import ZoneInfo
    _SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")
except Exception:
    _SAO_PAULO_TZ = timezone(timedelta(hours=-3))

UNITS: dict[str, str] = {
    "temperatura": "°C",
    "umidade": "%",
}


def _format_datetime(measured_at_iso: str) -> tuple[str | None, str]:
    try:
        dt = datetime.fromisoformat(measured_at_iso)
        if dt.tzinfo is not None:
            dt = dt.astimezone(_SAO_PAULO_TZ)
        return dt.strftime("%d/%m/%Y às %H:%M (Brasília)"), measured_at_iso
    except Exception:
        return None, measured_at_iso


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

        unit = UNITS.get(alert_type.strip().lower(), "")
        unit_suffix = f" {unit}" if unit else ""

        diff = abs(current_value - limit_value)
        pct = (diff / abs(limit_value) * 100) if limit_value != 0 else 0.0

        if current_value >= limit_value:
            excess_text = f"▲ {diff:.1f}{unit_suffix} acima do limite (+{pct:.1f}%)"
        else:
            excess_text = f"▼ {diff:.1f}{unit_suffix} abaixo do limite (-{pct:.1f}%)"

        preheader_text = f"{alert_type.capitalize()} em {current_value}{unit_suffix} — limite {limit_value}{unit_suffix}"

        formatted_br_date, raw_iso = _format_datetime(measured_at_iso)

        recommendation_text = (
            "Ação recomendada: verifique a alimentação elétrica e o posicionamento dos sensores "
            "para evitar leituras anômalas ou superaquecimento."
        )

        text = (
            "========================================================\n"
            "ALERTA DE TELEMETRIA OPERACIONAL - ELETROJUN\n"
            "========================================================\n\n"
            f"Tipo: {alert_type}\n"
            f"Valor atual: {current_value}{unit_suffix}\n"
            f"Limite: {limit_value}{unit_suffix}\n"
            f"Data/Hora: {measured_at_iso}\n"
            f"Origem MQTT: {source_topic}\n\n"
            "--------------------------------------------------------\n"
            "Status: LIMITE EXCEDIDO / ALERTA CRITICO\n"
            f"{recommendation_text}\n"
            "Notificacao automatica gerada pelo microsservico 'notifier'.\n"
            "========================================================"
        )

        safe_alert_type = html.escape(str(alert_type))
        safe_source_topic = html.escape(str(source_topic))
        safe_measured_at_iso = html.escape(str(measured_at_iso))
        safe_current_value = html.escape(str(current_value))
        safe_limit_value = html.escape(str(limit_value))
        safe_unit_suffix = html.escape(unit_suffix)
        safe_excess_text = html.escape(excess_text)
        safe_preheader = html.escape(preheader_text)
        safe_subject = html.escape(subject)

        if formatted_br_date:
            safe_formatted_date = html.escape(formatted_br_date)
            date_cell_html = (
                f'<div style="font-weight: 600; color: #0B0B0B;">{safe_formatted_date}</div>'
                f'<div style="font-family: ui-monospace, \'SF Mono\', Menlo, Monaco, Consolas, monospace; '
                f'font-size: 11px; color: #86868B; margin-top: 3px;">{safe_measured_at_iso}</div>'
            )
        else:
            date_cell_html = (
                f'<div style="font-family: ui-monospace, \'SF Mono\', Menlo, Monaco, Consolas, monospace; '
                f'font-size: 12px; color: #0B0B0B;">{safe_measured_at_iso}</div>'
            )

        email_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="light">
  <meta name="supported-color-schemes" content="light">
  <title>{safe_subject}</title>
  <style>
    :root {{
      color-scheme: light;
      supported-color-schemes: light;
    }}
    body, table, td, p, a, li, blockquote {{
      -webkit-text-size-adjust: 100%;
      -ms-text-size-adjust: 100%;
    }}
    body {{
      margin: 0;
      padding: 0;
      width: 100% !important;
      background-color: #F4F6F4;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      -webkit-font-smoothing: antialiased;
      color: #0B0B0B;
    }}
    h2 {{
      margin: 0;
      font-size: 20px;
      font-weight: 700;
      color: #0B0B0B;
      letter-spacing: -0.02em;
      line-height: 1.3;
    }}
    @media only screen and (max-width: 600px) {{
      .email-container {{
        width: 100% !important;
        padding: 16px 12px !important;
      }}
      .card-inner {{
        padding: 24px 18px !important;
      }}
      .telemetry-val {{
        font-size: 32px !important;
      }}
      .table-col-label {{
        width: 40% !important;
      }}
    }}
  </style>
</head>
<body style="margin: 0; padding: 0; background-color: #F4F6F4; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; color: #0B0B0B;">
  <!-- Preheader oculto para visualização na caixa de entrada -->
  <div style="display: none; max-height: 0px; overflow: hidden; mso-hide: all; font-size: 1px; line-height: 1px; color: #F4F6F4; opacity: 0;">
    {safe_preheader}
  </div>

  <!-- Wrapper Externo Centralizado -->
  <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #F4F6F4; width: 100%; margin: 0; padding: 40px 12px;">
    <tr>
      <td align="center">
        <!-- Container Principal (max-width: 580px) -->
        <table role="presentation" class="email-container" width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 580px; width: 100%; margin: 0 auto;">
          
          <!-- Card Principal com bordas suaves e overflow hidden -->
          <tr>
            <td style="background-color: #FFFFFF; border-radius: 16px; border: 1px solid #E3E8E3; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04); overflow: hidden;">
              
              <!-- Faixa Preta do Topo (Header EletroJun) -->
              <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #0B0B0B; width: 100%;">
                <tr>
                  <td style="padding: 20px 28px;">
                    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0">
                      <tr>
                        <td align="left" style="vertical-align: middle;">
                          <span style="font-size: 16px; font-weight: 800; letter-spacing: 0.12em; color: #FFFFFF; text-transform: uppercase;">EletroJun</span>
                          <span style="font-size: 13px; font-weight: 600; color: #00C853; margin-left: 8px;">Telemetria</span>
                        </td>
                        <td align="right" style="vertical-align: middle;">
                          <span style="display: inline-block; padding: 5px 12px; background-color: #1A0A0A; color: #FF4D4D; border: 1px solid #E5322D; border-radius: 9999px; font-size: 11px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; white-space: nowrap;">
                            &#9679; Alerta Crítico
                          </span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <!-- Linha de 3px verde logo abaixo da faixa preta -->
                <tr>
                  <td style="height: 3px; background-color: #00C853; font-size: 0; line-height: 0; padding: 0;">&nbsp;</td>
                </tr>
              </table>

              <!-- Conteúdo Interno do Card -->
              <table role="presentation" class="card-inner" width="100%" border="0" cellspacing="0" cellpadding="0" style="padding: 28px 32px;">
                
                <!-- Título e Contexto -->
                <tr>
                  <td>
                    <h2>Alerta de {safe_alert_type}</h2>
                    <p style="margin: 8px 0 0 0; font-size: 14px; line-height: 1.5; color: #6E6E73;">
                      O sistema de monitoramento registrou uma violação dos parâmetros operacionais definidos para a infraestrutura.
                    </p>
                  </td>
                </tr>

                <!-- Bloco de Destaque Telemetria (Hero Stat Block) -->
                <tr>
                  <td style="padding-top: 24px; padding-bottom: 24px;">
                    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #FAFCFA; border: 1px solid #E3E8E3; border-radius: 12px; text-align: center;">
                      <tr>
                        <td style="padding: 22px 16px;">
                          <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #6E6E73; margin-bottom: 6px;">
                            Valor Atual Medido
                          </div>
                          <div class="telemetry-val" style="font-size: 40px; font-weight: 800; color: #E5322D; letter-spacing: -0.03em; line-height: 1.1;">
                            {safe_current_value}{safe_unit_suffix}
                          </div>
                          <div style="font-size: 13px; color: #6E6E73; margin-top: 8px;">
                            Limite configurado: <strong style="color: #0B0B0B;">{safe_limit_value}{safe_unit_suffix}</strong>
                          </div>
                          <div style="font-size: 13px; font-weight: 600; color: #E5322D; margin-top: 6px;">
                            {safe_excess_text}
                          </div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <!-- Bloco de Especificações Técnicas -->
                <tr>
                  <td>
                    <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #6E6E73; margin-bottom: 12px;">
                      Especificações Técnicas
                    </div>
                    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="border-collapse: collapse; width: 100%;">
                      <tr style="border-top: 1px solid #E3E8E3; border-bottom: 1px solid #E3E8E3;">
                        <td class="table-col-label" style="padding: 12px 8px; font-size: 13px; color: #6E6E73; width: 35%;">Métrica</td>
                        <td style="padding: 12px 8px; font-size: 13px; font-weight: 600; color: #0B0B0B; text-transform: capitalize;">{safe_alert_type}</td>
                      </tr>
                      <tr style="border-bottom: 1px solid #E3E8E3;">
                        <td class="table-col-label" style="padding: 12px 8px; font-size: 13px; color: #6E6E73;">Tópico MQTT</td>
                        <td style="padding: 12px 8px; font-size: 12px;">
                          <code style="font-family: ui-monospace, 'SF Mono', Menlo, Monaco, Consolas, monospace; background-color: #F4F6F4; border: 1px solid #E3E8E3; padding: 3px 8px; border-radius: 6px; color: #0B0B0B; word-break: break-all;">{safe_source_topic}</code>
                        </td>
                      </tr>
                      <tr style="border-bottom: 1px solid #E3E8E3;">
                        <td class="table-col-label" style="padding: 12px 8px; font-size: 13px; color: #6E6E73; vertical-align: top;">Horário</td>
                        <td style="padding: 12px 8px; font-size: 13px; color: #0B0B0B;">
                          {date_cell_html}
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <!-- Caixa de Recomendação Operacional -->
                <tr>
                  <td style="padding-top: 24px;">
                    <div style="background-color: #F1F8F3; border-left: 3px solid #00C853; border-radius: 4px; padding: 14px 16px;">
                      <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #0B0B0B;">
                        <strong>Ação recomendada:</strong> verifique a alimentação elétrica e o posicionamento dos sensores para evitar leituras anômalas ou superaquecimento.
                      </p>
                    </div>
                  </td>
                </tr>

              </table>
            </td>
          </tr>

          <!-- Rodapé do E-mail -->
          <tr>
            <td align="center" style="padding-top: 24px; padding-bottom: 12px; text-align: center;">
              <p style="margin: 0 0 6px 0; font-size: 12px; font-weight: 600; color: #0B0B0B;">
                EletroJun • Divisão de IoT &amp; Automação
              </p>
              <p style="margin: 0 0 6px 0; font-size: 11px; color: #6E6E73; line-height: 1.4;">
                Notificação automática gerada pelo microsserviço <code style="font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; background-color: #E3E8E3; padding: 2px 6px; border-radius: 4px; color: #0B0B0B;">notifier</code>.
              </p>
              <p style="margin: 0; font-size: 11px; color: #86868B;">
                Este é um e-mail transacional do sistema. Respostas a este endereço não são monitoradas.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self._sender
        message["To"] = recipient
        message.set_content(text, cte="quoted-printable")
        message.add_alternative(email_html, subtype="html")

        smtp_factory = smtplib.SMTP_SSL if self._security == "tls" else smtplib.SMTP
        with smtp_factory(self._host, self._port, timeout=self._timeout_seconds) as smtp:
            smtp.ehlo()
            if self._security == "starttls":
                smtp.starttls()
                smtp.ehlo()
            if self._username:
                smtp.login(self._username, self._password or "")
            smtp.send_message(message)
