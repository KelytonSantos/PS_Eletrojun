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
  configTime(gmtOffset_sec, 0, ntpServer);

  pinMode(DHT_P, INPUT);
  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(LED3, OUTPUT);

  dht.begin();
  connect();
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

void connect() {}
void mqtt() {}
void callback(char *topic, byte *payload, unsigned int length) {}
void reconnectBroker() {}
Response mode(struct tm, unsigned long) {}
