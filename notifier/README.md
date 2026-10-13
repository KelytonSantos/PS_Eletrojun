# notifier

Microsserviço Python independente para envio de alertas de temperatura e umidade por e-mail.

O fluxo geral da arquitetura está documentado no
[README principal](../README.md).

## Funcionalidades

- Consome leituras MQTT do tópico configurável (`MQTT_SENSOR_TOPIC`, padrão `esp32_Eletrojun_Dht11/sensor`).
- Faz parsing rigoroso de payload CSV no formato `temperatura,umidade,data_hora`.
- Gerencia destinatários por HTTP:
  - `GET /api/alerts/emails`
  - `POST /api/alerts/email/{email}`
  - `DELETE /api/alerts/email/{email}`
- Gerencia limites por HTTP:
  - `GET /api/alerts/limits`
  - `POST /api/alerts/limits` (JSON `{ "temp": ..., "humi": ... }`)
  - `POST /api/alerts/limits?temp=...&humi=...`
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
- `SMTP_SECURITY` (`none`, `starttls` ou `tls`)
- `ALERT_CONFIG_FILE` ou `ALERT_DATABASE_URL`
- `ALERT_COOLDOWN_SECONDS`

### TLS/STARTTLS SMTP

- `SMTP_SECURITY=none`: conexão SMTP sem TLS explícito (compatível com SMTP local/falso de testes).
- `SMTP_SECURITY=starttls`: usa SMTP com upgrade STARTTLS.
- `SMTP_SECURITY=tls`: usa TLS implícito (SMTP sobre SSL, ex.: porta 465).

## Execução local

```bash
cd notifier
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m notifier.app
```

## Execução com Docker Compose

Na raiz do repositório, o Compose sobe o gateway Nginx na porta `8080`, a API
Java internamente na porta `8081` e o notifier internamente na porta `8082`.
O broker MQTT não é criado pelo Compose: os dois serviços conectam ao broker
externo definido por `MQTT_BROKER_HOST` (por padrão, `broker.hivemq.com`).

```bash
docker compose up --build
```

O app usa somente:

- `/api/realtime/*` para a API Java;
- `/api/alerts/*` para o notifier Python.

As credenciais SMTP continuam sendo lidas de `notifier/.env` pelo Compose.

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
