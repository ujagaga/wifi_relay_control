/*
 *  Author: Rada Berar
 *  email: ujagaga@gmail.com
 */
#include "config.h"
#include "pinctrl.h"
#include "wifi_connection.h"
#include <ArduinoJson.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266WiFi.h>
#include <ESP8266httpUpdate.h>
#include <WiFiClientSecure.h>

static unsigned long lastConnectAtemptTime = 0;
static int fail_count = 0;

void reportDeviceRequest() {
  if (WiFi.status() != WL_CONNECTED)
    return;

  HTTPClient http;
  WiFiClientSecure client;
  client.setInsecure(); // skip cert verification
  String url = String("https://") + REPORT_URL +
               "/device_report?name=" + WIFIC_getDeviceName();

  http.begin(client, url);
  int httpCode = http.GET();

  if (httpCode > 0) {
    String response = http.getString();
    response.trim();
    Serial.print("HTTP RX:");
    Serial.println(response);

    if (response.startsWith("{")) {
      StaticJsonDocument<256> doc;
      if (deserializeJson(doc, response) == DeserializationError::Ok) {
        const char *cmd = doc["command"];
        if (cmd) {
          if (strcmp(cmd, "unlock") == 0) {
#ifndef USE_MQTT
            int relay_id = doc["relay_id"] | 0;
            PINCTRL_trigger(relay_id);
#endif
          } else if (strcmp(cmd, "update") == 0) {
            const char *fw_path = doc["firmware"];
            if (fw_path && strlen(fw_path) > 0) {
              String fwUrl = String("https://") + REPORT_URL + String(fw_path);
              http.end();
              Serial.println("Starting OTA update from: " + fwUrl);

              WiFiClientSecure updateClient;
              updateClient.setInsecure();
              updateClient.setBufferSizes(512, 512);
              t_httpUpdate_return ret =
                  ESPhttpUpdate.update(updateClient, fwUrl);

              switch (ret) {
              case HTTP_UPDATE_FAILED:
                Serial.printf("OTA failed, error (%d): %s\n",
                              ESPhttpUpdate.getLastError(),
                              ESPhttpUpdate.getLastErrorString().c_str());
                break;
              case HTTP_UPDATE_NO_UPDATES:
                Serial.println("No update available.");
                break;
              case HTTP_UPDATE_OK:
                Serial.println("OTA OK, rebooting...");
                break; // reboot happens automatically
              }
            }
          } else if (strcmp(cmd, "restart") == 0) {
#ifndef USE_MQTT
            Serial.println("Restart command received.");
            ESP.restart();
#endif
          }
        }
      }
    }
  } else {
    Serial.printf("HTTP GET failed, error: %s\n",
                  http.errorToString(httpCode).c_str());
  }

  http.end();
  lastConnectAtemptTime = millis();
}

void HTTP_CLIENT_process() {
  if (((millis() - lastConnectAtemptTime) > (UPDATE_TIMEOUT + random(100))) ||
      (lastConnectAtemptTime == 0)) {
    reportDeviceRequest();
  }
}
