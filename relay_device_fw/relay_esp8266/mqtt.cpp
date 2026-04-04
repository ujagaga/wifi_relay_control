/*
 *  Author: Rada Berar
 *  email: ujagaga@gmail.com
 *
 *  MQTT client module to anounce itself to iot-portal and accept MQTT commands.
 */
#include "mqtt.h"
#include "config.h"
#include "pinctrl.h"
#include <ArduinoJson.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

#define CONNECT_TIMEOUT (10000ul)

WiFiClient espClient;
PubSubClient mqttclient(espClient);
static String macAddr = "";
static char msgBuffer[256] = {0};
static uint32_t connectAttemptTime = 0;
static char clientName[32] = {0};

static void callback(char *topic, byte *payload, unsigned int length) {

  char textMsg[length + 1] = {0};
  for (int i = 0; i < length; i++) {
    textMsg[i] = (char)payload[i];
  }

  StaticJsonDocument<128> doc;
  DeserializationError error = deserializeJson(doc, textMsg);

  if (!error) {
    const char* cmd = doc["command"];
    if (cmd) {
      if (strcmp(cmd, "unlock") == 0) {
        int relay_id = doc["relay_id"] | 0;
        PINCTRL_trigger(relay_id);
      } else if (strcmp(cmd, "restart") == 0) {
        Serial.println("Restart command received.");
        ESP.restart();
      }
    }
  }
}

static void mqtt_connect() {

  mqttclient.setServer(MQTT_URL, MQTT_PORT);
  mqttclient.setCallback(callback);
  // Attempt to connect
  if (mqttclient.connect(clientName)) {
    Serial.println("connected");
    mqttclient.subscribe(clientName);
  } else {
    Serial.print("MQTT failed. Server IP:");
    Serial.println(MQTT_URL);
    Serial.print("ERROR:");
    Serial.println(mqttclient.state());
  }
}

void MQTT_init() {
  macAddr = WiFi.macAddress();
  macAddr.replace(":", "");
  macAddr.toCharArray(clientName, sizeof(clientName));
  Serial.println("MQTT client name:" + macAddr);
  mqtt_connect();
}

void MQTT_process() {
  if (!mqttclient.connected() &&
      ((millis() - connectAttemptTime) > CONNECT_TIMEOUT)) {
    // Not connected. Try again.
    mqtt_connect();
    connectAttemptTime = millis();
  }

  mqttclient.loop();
}
