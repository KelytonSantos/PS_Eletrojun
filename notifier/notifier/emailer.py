from __future__ import annotations

import html
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
            "========================================================\n"
            "ALERTA DE TELEMETRIA OPERACIONAL - ELETROJUN\n"
            "========================================================\n\n"
            f"Tipo: {alert_type}\n"
            f"Valor atual: {current_value}\n"
            f"Limite: {limit_value}\n"
            f"Data/Hora: {measured_at_iso}\n"
            f"Origem MQTT: {source_topic}\n\n"
            "--------------------------------------------------------\n"
            "Status: LIMITE EXCEDIDO / ALERTA CRITICO\n"
            "Recomendacao: Inspecione os parametros do hardware e do ambiente.\n"
            "Notificacao automatica gerada pelo microsservico 'notifier'.\n"
            "========================================================"
        )

        safe_alert_type = html.escape(str(alert_type))
        safe_source_topic = html.escape(str(source_topic))
        safe_measured_at_iso = html.escape(str(measured_at_iso))
        safe_current_value = html.escape(str(current_value))
        safe_limit_value = html.escape(str(limit_value))

        email_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
  <style>
    body, table, td, p, a, li, blockquote {{
      -webkit-text-size-adjust: 100%;
      -ms-text-size-adjust: 100%;
    }}
    body {{
      margin: 0;
      padding: 0;
      width: 100% !important;
      background-color: #F5F5F7;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      -webkit-font-smoothing: antialiased;
    }}
    h2 {{
      margin: 0;
      font-size: 20px;
      font-weight: 700;
      color: #1D1D1F;
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
<body style="margin: 0; padding: 0; background-color: #F5F5F7; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; color: #1D1D1F;">
  <!-- Wrapper Externo Centralizado -->
  <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #F5F5F7; width: 100%; margin: 0; padding: 40px 12px;">
    <tr>
      <td align="center">
        <!-- Container Principal (max-width: 580px) -->
        <table role="presentation" class="email-container" width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 580px; width: 100%; margin: 0 auto;">
          
          <!-- Card Principal -->
          <tr>
            <td style="background-color: #FFFFFF; border-radius: 16px; border: 1px solid #E5E5EA; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05); overflow: hidden;">
              <table role="presentation" class="card-inner" width="100%" border="0" cellspacing="0" cellpadding="0" style="padding: 32px 32px 28px 32px;">
                
                <!-- Cabeçalho Executivo: Marca & Badge de Emergência -->
                <tr>
                  <td>
                    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0">
                      <tr>
                        <td align="left" style="vertical-align: middle;">
                          <div style="display: inline-block;">
                            <span style="font-size: 15px; font-weight: 800; letter-spacing: 0.08em; color: #1D1D1F; text-transform: uppercase;">EletroJun</span>
                            <span style="display: inline-block; margin-left: 6px; font-size: 12px; font-weight: 500; color: #86868B;">• Telemetria</span>
                          </div>
                        </td>
                        <td align="right" style="vertical-align: middle;">
                          <span style="display: inline-block; padding: 5px 12px; background-color: #FFE5E5; color: #FF3B30; border: 1px solid #FFD1D1; border-radius: 9999px; font-size: 11px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;">
                            &#9679; Alerta Crítico
                          </span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <!-- Divisor Sutil -->
                <tr>
                  <td style="padding-top: 20px; padding-bottom: 20px;">
                    <div style="height: 1px; background-color: #F2F2F7; width: 100%;"></div>
                  </td>
                </tr>

                <!-- Título e Contexto -->
                <tr>
                  <td>
                    <h2>Alerta de {safe_alert_type}</h2>
                    <p style="margin: 8px 0 0 0; font-size: 14px; line-height: 1.5; color: #6E6E73;">
                      O sistema de monitoramento registrou uma violação dos parâmetros operacionais definidos para a infraestrutura.
                    </p>
                  </td>
                </tr>

                <!-- Destaque do Valor Medido (Hero Telemetry Block) -->
                <tr>
                  <td style="padding-top: 24px; padding-bottom: 24px;">
                    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #FAFAFC; border: 1px solid #E5E5EA; border-radius: 12px; text-align: center;">
                      <tr>
                        <td style="padding: 22px 16px;">
                          <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #86868B; margin-bottom: 6px;">
                            Valor Atual Medido
                          </div>
                          <div class="telemetry-val" style="font-size: 40px; font-weight: 800; color: #FF3B30; letter-spacing: -0.03em; line-height: 1.1;">
                            {safe_current_value}
                          </div>
                          <div style="font-size: 13px; color: #86868B; margin-top: 8px;">
                            Limite Configurado: <span style="font-weight: 600; color: #1D1D1F;">{safe_limit_value}</span>
                          </div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <!-- Bloco de Telemetria Detalhada -->
                <tr>
                  <td>
                    <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #86868B; margin-bottom: 12px;">
                      Especificações Técnicas
                    </div>
                    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="border-collapse: collapse; width: 100%;">
                      <tr style="border-top: 1px solid #F2F2F7; border-bottom: 1px solid #F2F2F7;">
                        <td class="table-col-label" style="padding: 12px 8px; font-size: 13px; color: #6E6E73; width: 38%;">Métrica Monitorada</td>
                        <td style="padding: 12px 8px; font-size: 13px; font-weight: 600; color: #1D1D1F; text-transform: capitalize;">{safe_alert_type}</td>
                      </tr>
                      <tr style="border-bottom: 1px solid #F2F2F7;">
                        <td class="table-col-label" style="padding: 12px 8px; font-size: 13px; color: #6E6E73;">Valor Medido</td>
                        <td style="padding: 12px 8px; font-size: 13px; font-weight: 700; color: #FF3B30;">{safe_current_value}</td>
                      </tr>
                      <tr style="border-bottom: 1px solid #F2F2F7;">
                        <td class="table-col-label" style="padding: 12px 8px; font-size: 13px; color: #6E6E73;">Limite Tolerado</td>
                        <td style="padding: 12px 8px; font-size: 13px; font-weight: 600; color: #1D1D1F;">{safe_limit_value}</td>
                      </tr>
                      <tr style="border-bottom: 1px solid #F2F2F7;">
                        <td class="table-col-label" style="padding: 12px 8px; font-size: 13px; color: #6E6E73;">Tópico MQTT</td>
                        <td style="padding: 12px 8px; font-size: 12px;">
                          <code style="font-family: ui-monospace, 'SF Mono', Menlo, Monaco, Consolas, monospace; background-color: #F5F5F7; border: 1px solid #E5E5EA; padding: 3px 8px; border-radius: 6px; color: #1D1D1F; word-break: break-all;">{safe_source_topic}</code>
                        </td>
                      </tr>
                      <tr style="border-bottom: 1px solid #F2F2F7;">
                        <td class="table-col-label" style="padding: 12px 8px; font-size: 13px; color: #6E6E73;">Timestamp (ISO 8601)</td>
                        <td style="padding: 12px 8px; font-size: 12px; font-family: ui-monospace, 'SF Mono', Menlo, Monaco, Consolas, monospace; color: #48484A;">{safe_measured_at_iso}</td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <!-- Aviso de Ação / Recomendação Operacional -->
                <tr>
                  <td style="padding-top: 24px;">
                    <div style="background-color: #FFF9F2; border-left: 3px solid #FF9500; border-radius: 4px; padding: 12px 16px;">
                      <p style="margin: 0; font-size: 12px; line-height: 1.5; color: #8A5300;">
                        <strong>Ação Preventiva:</strong> Verifique o fornecimento e o posicionamento dos sensores para prevenir leituras anômalas ou superaquecimento.
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
              <p style="margin: 0 0 6px 0; font-size: 12px; font-weight: 600; color: #86868B;">
                EletroJun Engenharia • Divisão de IoT & Automação
              </p>
              <p style="margin: 0 0 6px 0; font-size: 11px; color: #86868B; line-height: 1.4;">
                Notificação automática gerada pelo microsserviço <code style="font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; background-color: #E5E5EA; padding: 1px 5px; border-radius: 4px; color: #1D1D1F;">notifier</code>.
              </p>
              <p style="margin: 0; font-size: 11px; color: #AEAEB2;">
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
        message.set_content(text)
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
