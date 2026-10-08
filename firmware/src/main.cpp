#include <Arduino.h>
#include <DHT.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "time.h"

//________________________________config de sistema
#define DHT_P 21
#define LED1 25
#define LED2 33
#define LED3 32

const char *ssid = "Not-A-Robot";
const char *pass = "20027477FLA";
const char *mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;
unsigned long lastMsg = 0;
const long gmtOffset_sec = -3 * 3600;
const char *ntpServer = "pool.ntp.br";

String actualMode = "AUTOMATICO";
bool pendingReading = false;
//_________________________________________________

//_______________________________struct de response
struct Response
{
  float humidity;
  float temperature;
  char formatedDate[20];
};
//_________________________________________________

//______________________________prototipo das funcs
void connect();
void mqtt();
void callback(char *topic, byte *payload, unsigned int length);
void reconnectBroker();
Response mode(struct tm, unsigned long);
//_________________________________________________

//_____________________________inicialização de obj
DHT dht(DHT_P, DHT11);
WiFiClient esp;
PubSubClient client(esp);
//_________________________________________________

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

void loop()
{

  Response response;
  struct tm timeinfo;

  if (!getLocalTime(&timeinfo))
  {
    Serial.println("Error retrieving the time");
    return;
  }
}
//_________________________________________________
void connect()
{
  WiFi.begin(ssid, pass);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.println(".");
  }
}
//_________________________________________________

//_________________________________________________
void mqtt()
{
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}
//_________________________________________________

void callback(char *topic, byte *payload, unsigned int length)
{
  String message = "";

  for (int i = 0; i < length; i++)
  {
    message += (char)payload;
  }

  if (String(topic) == "esp32_Eletrojun_Dht11/modo")
  {
    if (message == "DESLIGADO" || message == "LIGADO" || message == "AUTOMATICO")
    {
      actualMode = message;
      pendingReading = false;
      Serial.print("[MODE]: Updating to: ");
      Serial.println(actualMode);
    }

    else if (message == "LEITURA")
    {
      if (actualMode == "LIGADO")
      {
        pendingReading = true;
        Serial.println("[MODE] Manual Reading requested");
      }
      else
        Serial.println("[MODE] Command LEITURA ignored (not in LIGADO mode)");
    }
  }
}
//_________________________________________________

void reconnectBroker()
{
  while (!client.connected())
  {
    Serial.println("[MQTT] Trying to connect to the broker...");
    String clientId = "Esp32EletrojunDht11";

    if (client.connect(clientId.c_str()))
    {
      Serial.println("[MQTT] Connected");
      client.subscribe("esp32_Eletrojun_Dht11/modo");
      Serial.println("[MQTT] Subscribed: esp32_Eletrojun_Dht11/modo");
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
Response mode(struct tm, unsigned long) {}
