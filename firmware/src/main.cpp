/**
 * @file main.cpp
 * @brief Firmware embarcado no microcontrolador ESP32-WROOM-32U
 * @details Responsável pela coleta de temperatura e umidade com sensor DHT11,
 *          sincronização de horário via NTP, controle visual via LEDs e comunicação
 *          bidirecional via protocolo MQTT (publicação de leituras e recebimento de comandos).
 * 
 * Processo Seletivo Eletronjun 2026.2 - Projeto Leitor de Temperatura
 */

#include <Arduino.h>
#include <DHT.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "time.h"

// ============================================================================
// CONFIGURAÇÕES DE HARDWARE E PINOS
// ============================================================================
#define DHT_P 26      // Pino GPIO26 conectado ao barramento de dados do sensor DHT11
#define LED1 4        // Pino GPIO4 conectado ao LED1 (Indicador de Modo LIGADO / Manual)
#define LED2 5        // Pino GPIO5 conectado ao LED2 (Indicador de Modo AUTOMÁTICO)
#define LED3 21       // Pino GPIO21 conectado ao LED3 (Indicador de Modo DESLIGADO)

// ============================================================================
// CONFIGURAÇÕES DE REDE, NTP E BROKER MQTT
// ============================================================================
const char *ssid = "HeavensRoad";
const char *pass = "PSRMFKfR";
const char *mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;

// Tópicos MQTT utilizados pelo firmware
const char *TOPIC_SENSOR_PUB = "esp32_Eletrojun_Dht11/sensor"; // Tópico para publicar telemetria
const char *TOPIC_MODE_SUB   = "esp32_Eletrojun_Dht11/modo";   // Tópico para receber comandos

unsigned long lastMsg = 0;
const long gmtOffset_sec = -3 * 3600; // Fuso horário Brasília (UTC-3)
const char *ntpServer = "pool.ntp.br";

// Variáveis de controle de estado
String actualMode = "AUTOMATICO";    // Modo de operação inicial padrão
bool pendingReading = false;         // Flag que sinaliza requisição de leitura avulsa (Modo Ligado)

// ============================================================================
// ESTRUTURA DE DADOS DE RESPOSTA DO SENSOR
// ============================================================================
struct Response
{
  float humidity;         // Umidade relativa (%)
  float temperature;      // Temperatura ambiente (°C)
  char formatedDate[20];  // Timestamp formatado (ISO 8601: YYYY-MM-DDTHH:MM:SS)
};

// ============================================================================
// PROTÓTIPOS DAS FUNÇÕES
// ============================================================================
void connect();
void mqtt();
void callback(char *topic, byte *payload, unsigned int length);
void reconnectBroker();
Response mode(struct tm timeInfo, unsigned long now);

// ============================================================================
// INSTANCIAÇÃO DOS COMPONENTES E CLIENTES
// ============================================================================
DHT dht(DHT_P, DHT11);
WiFiClient esp;
PubSubClient client(esp);

/**
 * @brief Configuração inicial do hardware e dos serviços de rede.
 * Inicializa a porta serial para depuração, conecta ao Wi-Fi, sincroniza o
 * relógio via NTP, configura as direções dos pinos GPIO, inicia o sensor DHT
 * e configura o cliente MQTT.
 */
void setup()
{
  Serial.begin(115200);
  connect();
  configTime(gmtOffset_sec, 0, ntpServer);

  pinMode(DHT_P, INPUT);
  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(LED3, OUTPUT);

  dht.begin();
  mqtt();
}

/**
 * @brief Laço de execução contínuo do microcontrolador.
 * Mantém a integridade da conexão MQTT, processa pacotes pendentes, obtém o horário
 * local, valida as leituras do sensor DHT11 e despacha o controle para a máquina de estados.
 */
void loop()
{
  Response response;
  struct tm timeinfo;

  // Garante que o horário local está sincronizado
  if (!getLocalTime(&timeinfo))
  {
    Serial.println("Error retrieving the time");
    return;
  }

  // Verifica e restabelece a conexão com o broker MQTT se necessário
  if (!client.connected())
  {
    reconnectBroker();
  }
  client.loop(); // Processa mensagens MQTT recebidas e mantém o ping/keepalive ativo

  // Validação de integridade física da leitura do sensor
  if (isnan(dht.readTemperature()) || isnan(dht.readHumidity()))
  {
    Serial.println("Not A Number");
    delay(1000);
    return;
  }

  unsigned long now = millis();

  // Executa a lógica de controle correspondente ao modo atual
  response = mode(timeinfo, now);

  delay(1000);
}

/**
 * @brief Inicializa e gerencia a conexão Wi-Fi do ESP32.
 * Bloqueia a execução com tentativas a cada 500ms até que o status seja WL_CONNECTED.
 */
void connect()
{
  WiFi.begin(ssid, pass);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.println(".");
  }
  Serial.println("[WIFI] Conectado com sucesso!");
}

/**
 * @brief Inicializa as configurações do cliente MQTT.
 * Define o endereço do servidor broker externo, a porta de conexão e a função de callback
 * que será invocada sempre que uma mensagem for recebida em tópicos inscritos.
 */
void mqtt()
{
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

/**
 * @brief Callback de recebimento de comandos via broker MQTT (Chamada de API/Mensageria).
 * É disparado assincronamente quando uma mensagem chega no tópico de controle.
 * 
 * @param topic Nome do tópico MQTT onde a mensagem foi publicada.
 * @param payload Conteúdo binário da mensagem recebida.
 * @param length Tamanho em bytes do payload.
 */
void callback(char *topic, byte *payload, unsigned int length)
{
  String message = "";

  for (int i = 0; i < length; i++)
  {
    message += (char)payload[i];
  }

  // Processamento de comandos enviados ao tópico de modos
  if (String(topic) == TOPIC_MODE_SUB)
  {
    // Comutação para os modos do sistema: DESLIGADO, LIGADO ou AUTOMATICO
    if (message == "DESLIGADO" || message == "LIGADO" || message == "AUTOMATICO")
    {
      actualMode = message;
      pendingReading = false;
      Serial.print("[MODE]: Updating to: ");
      Serial.println(actualMode);
    }
    // Comando de leitura sob demanda (permitido exclusivamente em modo LIGADO)
    else if (message == "LEITURA")
    {
      if (actualMode == "LIGADO")
      {
        pendingReading = true;
        Serial.println("[MODE] Manual Reading requested");
      }
      else
      {
        Serial.println("[MODE] Command LEITURA ignored (not in LIGADO mode)");
      }
    }
  }
}

/**
 * @brief Reconexão resiliente ao Broker MQTT.
 * Caso a conexão com o broker seja interrompida, tenta reconectar a cada 5 segundos
 * e se reinscreve automaticamente no tópico de comandos ("esp32_Eletrojun_Dht11/modo").
 */
void reconnectBroker()
{
  while (!client.connected())
  {
    Serial.println("[MQTT] Trying to connect to the broker...");
    String clientId = "Esp32EletrojunDht11";

    if (client.connect(clientId.c_str()))
    {
      Serial.println("[MQTT] Connected");
      client.subscribe(TOPIC_MODE_SUB);
      Serial.print("[MQTT] Subscribed: ");
      Serial.println(TOPIC_MODE_SUB);
    }
    else
    {
      Serial.print("[MQTT] Error, rc=");
      Serial.print(client.state());
      Serial.println(" | Trying again in 5s...");
      delay(5000);
    }
  }
}

/**
 * @brief Máquina de estados do protótipo e controle de atuadores luminosos (LEDs).
 * - MODO DESLIGADO: LED3 ligado; sensor e telemetria inativos.
 * - MODO LIGADO (Manual): LED1 ligado; realiza e publica leituras sob demanda manual ("LEITURA").
 * - MODO AUTOMÁTICO: LED2 ligado; realiza leituras e publica periodicamente a cada 5 segundos.
 * 
 * @param timeInfo Estrutura com data e hora atual sincronizada via NTP.
 * @param now Timestamp em milissegundos retornado por millis().
 * @return Response Estrutura preenchida com valores de temperatura, umidade e data formatada.
 */
Response mode(struct tm timeInfo, unsigned long now)
{
  Response response;

  strftime(response.formatedDate, sizeof(response.formatedDate), "%Y-%m-%dT%H:%M:%S", &timeInfo);
  response.temperature = dht.readTemperature();
  response.humidity = dht.readHumidity();

  // ESTADO 1: DESLIGADO (RF03)
  if (actualMode == "DESLIGADO")
  {
    digitalWrite(LED3, HIGH);
    digitalWrite(LED2, LOW);
    digitalWrite(LED1, LOW);

    return response;
  }

  // ESTADO 2: LIGADO / MANUAL (RF04)
  if (actualMode == "LIGADO")
  {
    digitalWrite(LED1, HIGH);
    digitalWrite(LED2, LOW);
    digitalWrite(LED3, LOW);

    if (pendingReading)
    {
      pendingReading = false;
      String payload = String(response.temperature) + "," + String(response.humidity) + "," + response.formatedDate;
      Serial.printf("[LIGADO] T: %.1f H: %.1f Hora: %s\n", response.temperature, response.humidity, response.formatedDate);
      client.publish(TOPIC_SENSOR_PUB, payload.c_str());
    }
    return response;
  }

  // ESTADO 3: AUTOMÁTICO (RF05)
  digitalWrite(LED2, HIGH);
  digitalWrite(LED1, LOW);
  digitalWrite(LED3, LOW);

  // Streaming contínuo a cada 5 segundos (5000ms)
  if (now - lastMsg > 5000)
  {
    lastMsg = now;
    String payload = String(response.temperature) + "," + String(response.humidity) + "," + response.formatedDate;
    Serial.printf("[AUTO] T: %.1f H: %.1f Hora: %s\n", response.temperature, response.humidity, response.formatedDate);
    client.publish(TOPIC_SENSOR_PUB, payload.c_str());
  }

  return response;
}
