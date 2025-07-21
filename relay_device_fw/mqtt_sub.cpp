#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "config.h"
#include "wifi_connection.h"
#include "web_socket.h"
#include "http_server.h"
#include "pinctrl.h"

void mqtt_callback(char* topic, byte* payload, unsigned int length);

WiFiClient espClient;
static PubSubClient mqtt_client(MQTT_SERVER, MQTT_PORT, mqtt_callback, espClient);
static long last_connect_attempt_timestamp = 0;
static int fail_count = 0;

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();

  // Allocate a JSON document
  StaticJsonDocument<200> doc;

  // Parse payload
  DeserializationError error = deserializeJson(doc, payload, length);
  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.f_str());
    return;
  }

  const char* host = doc["host"];
  const char* command = doc["command"];  

  const char* deviceName = WIFIC_getDeviceName();

  // Compare host
  if (strcmp(host, deviceName) == 0) {
    if (strcmp(command, "trigger") == 0) {
      const char* relay_id_str = doc["relay_id"];
      int relay_id = atoi(relay_id_str);
      PINCTRL_trigger(relay_id); 

    } else if (strcmp(command, "restart") == 0) {
      Serial.println("Restarting device...");
      ESP.restart();
    }
  } 
}

void MQTT_process() {
  // Retry every 60 seconds
  if (!mqtt_client.connected() && ((millis() - last_connect_attempt_timestamp) > 60000)) {
    Serial.print("Attempting MQTT connection...");

    char* deviceName = WIFIC_getDeviceName();

    if (mqtt_client.connect(deviceName, MQTT_USER, MQTT_PASS)) {
      Serial.println("connected");
      mqtt_client.subscribe(MQTT_TOPIC);
      fail_count = 0;
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqtt_client.state());
      fail_count++;
      if(fail_count>4){
        // Restarting after 5 failed attempts
        ESP.restart();
      }
    }
    last_connect_attempt_timestamp = millis();
  }
  mqtt_client.loop();
}
