# notifier

Microsserviço Python independente para envio de alertas de temperatura e umidade por e-mail.

## Funcionalidades

- Consome leituras MQTT do tópico configurável (`MQTT_SENSOR_TOPIC`, padrão `esp32_Eletrojun_Dht11/sensor`).
- Faz parsing rigoroso de payload CSV no formato `temperatura,umidade,data_hora`.
- Gerencia destinatários por HTTP:
  - `GET /api/realtime/emails`
  - `POST /api/realtime/email/{email}`
  - `DELETE /api/realtime/email/{email}`
- Gerencia limites por HTTP:
  - `GET /api/realtime/limits`
  - `POST /api/realtime/limits` (JSON `{ "temp": ..., "humi": ... }`)
  - `POST /api/realtime/limits?temp=...&humi=...`
- Persistência em SQLite (arquivo configurável via `ALERT_CONFIG_FILE` ou `ALERT_DATABASE_URL`).
- Envia e-mails com corpo texto e HTML.
- Cooldown configurável (`ALERT_COOLDOWN_SECONDS`) com normalização de estado.
- Falhas de envio são tratadas por destinatário, sem interromper os demais.

## Configuração

Copie `.env.example` para `.env` no ambiente desejado e defina as variáveis.

Variáveis mínimas:

- `MQTT_BROKER_URL`
- `MQTT_PORT`
- `MQTT_USERNAME`
- `MQTT_PASSWORD`
- `MQTT_SENSOR_TOPIC`
- `MQTT_CLIENT_ID`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM`
- `ALERT_CONFIG_FILE` ou `ALERT_DATABASE_URL`
- `ALERT_COOLDOWN_SECONDS`

## Execução local

```bash
cd notifier
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m notifier.app
```

## Testes

```bash
cd notifier
pytest -q
```

## Decisões técnicas

- Persistência: SQLite local para suportar reinicialização sem dependências externas.
- MQTT: cliente `paho-mqtt` com `loop_start`, callback de reconexão e reassinatura no `on_connect`.
- Não bloqueio do consumo: processamento assíncrono de mensagens em `ThreadPoolExecutor` e timeout no SMTP.
- Segurança: segredos só por ambiente; logs e respostas não incluem credenciais.
