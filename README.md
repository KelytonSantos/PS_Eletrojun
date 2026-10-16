# Eletrojun

Sistema distribuído para controlar o modo de operação do dispositivo, receber
leituras MQTT, registrar o histórico e enviar alertas.

## Arquitetura

```text
FLUXO HTTP

Cliente HTTP
    |
    v
Gateway Nginx :8080
    |------------------------------|
    v                              v
API Java :8081                Notifier :8082
(/api/realtime)               (/api/alerts)


FLUXO MQTT

ESP32 <------> MQTT broker externo <------> API Java
  |                    |                      |
  |                    |                      +-- publica comandos
  |                    |
  |                    +--------------------> Logger Python
  |                    |                       grava /data/LogEsp.txt
  |                    |
  |                    +--------------------> Notifier Python
  |                                            envia alertas por e-mail
  |
  +-- publica leituras de temperatura e umidade
```

### Módulos

- **`app/`**: aplicativo móvel Android (Capacitor); monitoramento em tempo real, histórico e ajustes de alertas. Inclui o instalador pronto [`app/app-debug.apk`](./app/app-debug.apk).
- **`firmware/`**: firmware do ESP32; publica leituras e recebe comandos via MQTT.
- **`api/`**: API Java/Spring Boot; consulta o estado e publica comandos MQTT.
- **`logger/`**: consumidor Python/Paho; valida as leituras e grava `LogEsp.txt`.
- **`notifier/`**: consumidor Python; controla limites, destinatários e alertas por e-mail.
- **`nginx/`**: gateway reverso que centraliza o acesso HTTP na porta `8080`.
- **`compose.yaml`**: orquestra os serviços; o broker MQTT continua externo.

A separação foi escolhida exclusivamente para facilitar escala independente e
permitir livre escolha de stack por cada desenvolvedor ou módulo. Assim, cada
serviço pode evoluir, ser escalado e receber manutenção sem obrigar todo o
projeto a usar a mesma tecnologia.

## Configuração

Somente arquivos `.env.example` devem ser versionados. Os arquivos `.env` são
locais e estão ignorados pelo Git.

```bash
cp .env.example .env
cp logger/.env.example logger/.env
cp notifier/.env.example notifier/.env
```

Preencha as credenciais SMTP em `notifier/.env` antes de iniciar o notifier.
Nunca coloque senhas ou tokens nos arquivos `.env.example`.

## Executar com Docker Compose

Na raiz do projeto:

```bash
docker compose build
docker compose up -d
docker compose ps
```

Para acompanhar todos os serviços:

```bash
docker compose logs -f
```

Para parar os serviços:

```bash
docker compose down
```

## Acessar o logger

O logger não possui endpoint HTTP. Ele consome o tópico MQTT e grava o arquivo
em `/data/LogEsp.txt` dentro do container, com persistência no volume Docker
`logger-data`.

Logs operacionais:

```bash
docker compose logs -f logger
```

Conteúdo do arquivo:

```bash
docker compose exec logger sh -c 'ls -la /data && tail -f /data/LogEsp.txt'
```

Para localizar a pasta física do volume no host:

```bash
docker volume inspect project_struct_logger-data
```

Também é possível copiar o arquivo para a pasta atual:

```bash
docker compose cp logger:/data/LogEsp.txt ./LogEsp.txt
```

## Acesso HTTP

O gateway fica disponível em `http://localhost:8080`:

- `http://localhost:8080/api/realtime/` encaminha para a API Java.
- `http://localhost:8080/api/alerts/` encaminha para o notifier.

As portas internas `8081` e `8082` não são publicadas diretamente no host.

## Testes locais

```bash
cd logger && python -m pytest -q
cd ../notifier && python -m pytest -q
```

## Documentação da API e MQTT

Para a especificação completa de todas as rotas HTTP, payloads de requisição/resposta, eventos SSE, tópicos e mensagens MQTT com exemplos em cURL, consulte o arquivo dedicado:

👉 **[Documentação Completa da API e MQTT (api.md)](./api.md)**

### Resumo Rápido de Rotas e Tópicos

| Protocolo | Rota / Tópico | Método / Tipo | Descrição |
| :--- | :--- | :--- | :--- |
| **HTTP** | `/api/realtime/mode` | `GET` | Consulta o modo operacional atual e conectividade MQTT |
| **HTTP** | `/api/realtime/mode/{mode}` | `POST` | Alterna modo (`AUTOMATICO`, `LIGADO`, `DESLIGADO`, `LEITURA`) |
| **HTTP** | `/api/realtime/history` | `GET` | Retorna buffer com histórico das últimas medições |
| **HTTP** | `/api/realtime/automatico/stream` | `GET (SSE)` | Streaming reativo contínuo via Server-Sent Events |
| **HTTP** | `/api/alerts/limits` | `GET / POST` | Consulta ou define limiares de alerta de temperatura e umidade |
| **HTTP** | `/api/alerts/emails` | `GET` | Lista e-mails cadastrados para receber notificações |
| **HTTP** | `/api/alerts/email/{email}` | `POST / DELETE` | Cadastra ou remove e-mails de alerta no banco SQLite |
| **MQTT** | `esp32_Eletrojun_Dht11/sensor` | Pub / Sub | Telemetria enviada pelo ESP32 (`temp,umidade,timestamp`) |
| **MQTT** | `esp32_Eletrojun_Dht11/modo` | Pub / Sub | Comandos enviados ao ESP32 (`AUTOMATICO`, `LIGADO`, `DESLIGADO`, `LEITURA`) |

