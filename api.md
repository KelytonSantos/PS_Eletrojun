# Documentação de API e Mensageria (MQTT)

Este documento descreve detalhadamente todos os endpoints HTTP expostos pelo Gateway Nginx (porta `8080`), bem como a arquitetura de mensageria assíncrona baseada em tópicos MQTT.

---

## Índice

1. [Visão Geral da Arquitetura](#visão-geral-da-arquitetura)
2. [Endpoints HTTP (REST e SSE)](#endpoints-http-rest-e-sse)
   - [API Java (Tempo Real e Modos)](#api-java-tempo-real-e-modos)
     - [`GET /api/realtime/mode`](#get-apirealtimemode)
     - [`POST /api/realtime/mode/{mode}`](#post-apirealtimemodemode)
     - [`GET /api/realtime/history`](#get-apirealtimehistory)
     - [`GET /api/realtime/automatico/stream` (SSE)](#get-apirealtimeautomaticostream-sse)
   - [Notifier Python (Limites e Alertas)](#notifier-python-limites-e-alertas)
     - [`GET /api/alerts/limits`](#get-apialertslimits)
     - [`POST /api/alerts/limits`](#post-apialertslimits)
     - [`GET /api/alerts/emails`](#get-apialertsemails)
     - [`POST /api/alerts/email/{email}`](#post-apialertsemailemail)
     - [`DELETE /api/alerts/email/{email}`](#delete-apialertsemailemail)
3. [Protocolo de Mensageria MQTT](#protocolo-de-mensageria-mqtt)
   - [Broker e Conectividade](#broker-e-conectividade)
   - [Tópico de Telemetria (`sensor`)](#tópico-de-telemetria-sensor)
   - [Tópico de Comandos (`modo`)](#tópico-de-comandos-modo)
4. [Exemplos Práticos com cURL](#exemplos-práticos-com-curl)

---

## Visão Geral da Arquitetura

O sistema utiliza o **Gateway Nginx** (`http://localhost:8080`) como ponto de entrada único para as requisições HTTP da aplicação móvel ou web, roteando internamente para os microsserviços correspondentes:

- `/api/realtime/*` $\rightarrow$ **API Java (Spring Boot)** na porta interna `8081`
- `/api/alerts/*` $\rightarrow$ **Notifier (Python / Flask)** na porta interna `8082`

Em paralelo, a comunicação entre o hardware (**ESP32**) e o ecossistema de microsserviços (**API Java**, **Logger** e **Notifier**) ocorre via **Broker MQTT**.

---

## Endpoints HTTP (REST e SSE)

### API Java (Tempo Real e Modos)

#### `GET /api/realtime/mode`
Consulta o modo de operação atual do dispositivo e o status da conexão MQTT da API.

- **Método:** `GET`
- **URL:** `http://localhost:8080/api/realtime/mode`
- **Headers:** Não requer autenticação. Suporta CORS.
- **Resposta de Sucesso (200 OK):**
  ```json
  {
    "mode": "AUTOMATICO",
    "mqttConnected": true
  }
  ```
  *Valores possíveis para `mode`:* `"AUTOMATICO"`, `"LIGADO"`, `"DESLIGADO"`.

---

#### `POST /api/realtime/mode/{mode}`
Altera o modo operacional do sistema ou dispara uma leitura manual sob demanda.

- **Método:** `POST`
- **URL:** `http://localhost:8080/api/realtime/mode/{mode}`
- **Parâmetros de Path:**
  - `mode` *(string, obrigatório)*:
    - `"AUTOMATICO"`: Ativa amostragem periódica contínua a cada 5 segundos (LED verde).
    - `"LIGADO"`: Ativa modo manual (LED amarelo). Leituras só ocorrem sob demanda.
    - `"DESLIGADO"`: Desativa sensores e telemetria (LED vermelho).
    - `"LEITURA"`: Solicita leitura manual imediata (permitido apenas quando o dispositivo estiver no modo `LIGADO`).
- **Respostas:**
  - **200 OK** (Modo alterado com sucesso):
    ```json
    {
      "status": "SUCCESS",
      "mode": "LIGADO",
      "message": "Modo atualizado com sucesso."
    }
    ```
  - **200 OK** (Solicitação de leitura sob demanda):
    ```json
    {
      "status": "SUCCESS",
      "mode": "LIGADO",
      "message": "Solicitação de leitura manual enviada ao dispositivo."
    }
    ```
  - **400 Bad Request** (Modo inválido ou leitura manual fora do modo LIGADO):
    ```json
    {
      "status": "ERROR",
      "message": "Leitura manual só é permitida quando o dispositivo estiver no modo LIGADO (modo atual: DESLIGADO)."
    }
    ```
  - **503 Service Unavailable** (Broker MQTT inacessível):
    ```json
    {
      "status": "ERROR",
      "message": "Broker MQTT indisponível para aplicar a alteração de modo."
    }
    ```

---

#### `GET /api/realtime/history`
Retorna as últimas leituras de telemetria recebidas e mantidas em memória (buffer de até 100 registros), ordenadas da mais recente para a mais antiga.

- **Método:** `GET`
- **URL:** `http://localhost:8080/api/realtime/history`
- **Resposta de Sucesso (200 OK):**
  ```json
  [
    {
      "temperature": 28.2,
      "humidity": 65.0,
      "dateAndTime": "2026-10-16T15:49:19"
    },
    {
      "temperature": 28.1,
      "humidity": 64.8,
      "dateAndTime": "2026-10-16T15:49:14"
    }
  ]
  ```

---

#### `GET /api/realtime/automatico/stream` (SSE)
Canal persistente de streaming via *Server-Sent Events* (SSE). Emite eventos a cada nova medição publicada pelo ESP32.

- **Método:** `GET`
- **URL:** `http://localhost:8080/api/realtime/automatico/stream`
- **Headers de Resposta:** `Content-Type: text/event-stream;charset=UTF-8`
- **Formato dos Eventos Emitidos:**
  ```text
  event: sensor-readings
  data: {"temperature":28.2,"humidity":65.0,"dateAndTime":"2026-10-16T15:49:19"}
  ```

---

### Notifier Python (Limites e Alertas)

#### `GET /api/alerts/limits`
Retorna os limiares atuais de temperatura máxima permitida e umidade mínima tolerada.

- **Método:** `GET`
- **URL:** `http://localhost:8080/api/alerts/limits`
- **Resposta de Sucesso (200 OK):**
  ```json
  {
    "tempMax": 30.0,
    "humiMin": 20.0
  }
  ```

---

#### `POST /api/alerts/limits`
Atualiza dinamicamente os limiares de alerta.

- **Método:** `POST`
- **URL:** `http://localhost:8080/api/alerts/limits`
- **Headers:** `Content-Type: application/json`
- **Payload (JSON Body):**
  ```json
  {
    "temp": 32.5,
    "humi": 25.0
  }
  ```
  *(Também suporta parâmetros via query string: `?temp=32.5&humi=25.0`)*
- **Resposta de Sucesso (200 OK):**
  ```json
  {
    "success": true,
    "tempMax": 32.5,
    "humiMin": 25.0
  }
  ```
- **Resposta de Erro (400 Bad Request):**
  ```json
  {
    "success": false,
    "error": "temp e humi são obrigatórios, finitos e dentro das faixas permitidas"
  }
  ```

---

#### `GET /api/alerts/emails`
Lista todos os endereços de e-mail cadastrados no banco de dados SQLite para recebimento de alertas SMTP.

- **Método:** `GET`
- **URL:** `http://localhost:8080/api/alerts/emails`
- **Resposta de Sucesso (200 OK):**
  ```json
  {
    "success": true,
    "emails": [
      "usuario@dominio.com",
      "engenharia@eletronjun.com.br"
    ]
  }
  ```

---

#### `POST /api/alerts/email/{email}`
Adiciona um novo e-mail à lista de destinatários de notificações de emergência.

- **Método:** `POST`
- **URL:** `http://localhost:8080/api/alerts/email/{email}`
- **Exemplo:** `POST http://localhost:8080/api/alerts/email/equipe@eletronjun.com.br`
- **Resposta de Sucesso (200 OK):**
  ```json
  {
    "success": true,
    "emails": [
      "usuario@dominio.com",
      "engenharia@eletronjun.com.br",
      "equipe@eletronjun.com.br"
    ]
  }
  ```
- **Resposta de Erro (400 Bad Request):**
  ```json
  {
    "success": false,
    "error": "Email vazio, inválido ou já cadastrado"
  }
  ```

---

#### `DELETE /api/alerts/email/{email}`
Remove um endereço de e-mail previamente cadastrado.

- **Método:** `DELETE`
- **URL:** `http://localhost:8080/api/alerts/email/{email}`
- **Exemplo:** `DELETE http://localhost:8080/api/alerts/email/usuario@dominio.com`
- **Resposta de Sucesso (200 OK):**
  ```json
  {
    "success": true,
    "emails": [
      "engenharia@eletronjun.com.br",
      "equipe@eletronjun.com.br"
    ]
  }
  ```
- **Resposta de Erro (400 Bad Request):**
  ```json
  {
    "success": false,
    "error": "Email vazio ou inválido"
  }
  ```

---

## Protocolo de Mensageria MQTT

### Broker e Conectividade
- **Servidor:** `broker.hivemq.com`
- **Porta:** `1883` (TCP padrão sem TLS)
- **QoS:** `1` (At least once) para comandos e telemetria

```
+-----------------------------------------------------------------------------------+
|                                BROKER MQTT EXTERNO                                |
|                             (broker.hivemq.com:1883)                              |
+-----------------------------------------------------------------------------------+
             ^                                      |
             | PUBLICA (Telemetria)                 | ASSINA (esp32_.../sensor)
             |                                      v
     [ESP32 FIRMWARE]              +----------------------------------+
             ^                     | • API Java (Repassa via SSE)     |
             | ASSINA (Comandos)   | • Logger Python (Grava arquivo)  |
             |                     | • Notifier Python (Alerta Email) |
             |                     +----------------------------------+
             |                                      ^
             +--------------------------------------+
                     PUBLICA COMANDOS (esp32_.../modo)
```

---

### Tópico de Telemetria (`sensor`)

- **Tópico:** `esp32_Eletrojun_Dht11/sensor`
- **Direção:** ESP32 $\rightarrow$ Broker MQTT $\rightarrow$ Assinantes (API Java, Logger, Notifier)
- **Frequência de Envio:**
  - Modo `AUTOMATICO`: a cada 5 segundos (5000 ms).
  - Modo `LIGADO`: sob demanda mediante publicação do comando `"LEITURA"`.
  - Modo `DESLIGADO`: não há publicações.
- **Formato do Payload:** String no padrão CSV:
  ```text
  <temperatura>,<umidade>,<timestamp_ISO8601>
  ```
- **Exemplo de Payload:**
  ```text
  28.20,65.00,2026-10-16T15:49:19
  ```
- **Campos:**
  1. `temperatura`: float em graus Celsius com 1 a 2 casas decimais.
  2. `umidade`: float de umidade relativa em percentual (`%`).
  3. `timestamp_ISO8601`: data e hora sincronizadas via NTP (`pool.ntp.br`, fuso UTC-3) no padrão `YYYY-MM-DDTHH:MM:SS`.

---

### Tópico de Comandos (`modo`)

- **Tópico:** `esp32_Eletrojun_Dht11/modo`
- **Direção:** API Java $\rightarrow$ Broker MQTT $\rightarrow$ ESP32
- **Formato do Payload:** String de texto simples (UTF-8).
- **Valores Permitidos:**
  | Comando | Descrição | Ação no Hardware |
  | :--- | :--- | :--- |
  | `AUTOMATICO` | Ativa monitoramento contínuo periódico | Acende **LED2** (Verde). ESP32 transmite telemetria a cada 5s. |
  | `LIGADO` | Ativa modo manual | Acende **LED1** (Amarelo). Permite comandos de leitura avulsa. |
  | `DESLIGADO` | Desativa medições e transmissão | Acende **LED3** (Vermelho). Sensores ficam inativos. |
  | `LEITURA` | Dispara amostragem sob demanda | Executado somente se o ESP32 estiver em modo `LIGADO`. Faz a leitura física do DHT11 e publica imediatamente no tópico de telemetria. |

---

## Exemplos Práticos com cURL

### 1. Consultar modo atual:
```bash
curl -X GET http://localhost:8080/api/realtime/mode
```

### 2. Mudar para Modo Automático:
```bash
curl -X POST http://localhost:8080/api/realtime/mode/AUTOMATICO
```

### 3. Mudar para Modo Ligado e solicitar leitura manual:
```bash
# 1. Comutar para LIGADO
curl -X POST http://localhost:8080/api/realtime/mode/LIGADO

# 2. Solicitar leitura sob demanda
curl -X POST http://localhost:8080/api/realtime/mode/LEITURA
```

### 4. Consultar histórico de medições:
```bash
curl -X GET http://localhost:8080/api/realtime/history
```

### 5. Atualizar limiares de alerta de temperatura e umidade:
```bash
curl -X POST http://localhost:8080/api/alerts/limits \
  -H "Content-Type: application/json" \
  -d '{"temp": 32.0, "humi": 25.0}'
```

### 6. Cadastrar e listar e-mails de alerta:
```bash
# Cadastrar e-mail
curl -X POST http://localhost:8080/api/alerts/email/admin@empresa.com

# Listar e-mails cadastrados
curl -X GET http://localhost:8080/api/alerts/emails
```

### 7. Ouvir fluxo em tempo real (SSE):
```bash
curl -N http://localhost:8080/api/realtime/automatico/stream
```
