/*
 *  Author: Rada Berar
 *  email: ujagaga@gmail.com
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <Update.h>
#include <ArduinoJson.h>
#include "config.h"
#include "wifi_connection.h"
#include "pinctrl.h"

static unsigned long lastConnectAtemptTime = 0;
static int fail_count = 0;

void performOtaUpdate(const String& fwUrl) {
  WiFiClient updateClient;
  HTTPClient http;

  Serial.println("Starting OTA update from: " + fwUrl);

  http.begin(updateClient, fwUrl);
  int httpCode = http.GET();

  if (httpCode == HTTP_CODE_OK) {
    int contentLength = http.getSize();
    bool canBegin = Update.begin(contentLength);

    if (canBegin) {
      WiFiClient* stream = http.getStreamPtr();
      size_t written = Update.writeStream(*stream);

      if (written == contentLength) {
        Serial.println("OTA written successfully, size: " + String(written));
      } else {
        Serial.println("OTA write failed! Written only: " + String(written) + " / " + String(contentLength));
      }

      if (Update.end()) {
        if (Update.isFinished()) {
          Serial.println("OTA update complete. Rebooting...");
          delay(500);
          ESP.restart();
        } else {
          Serial.println("OTA not finished. Something went wrong!");
        }
      } else {
        Serial.printf("OTA end error (%d): %s\n", Update.getError(), Update.errorString());
      }
    } else {
      Serial.println("Not enough space for OTA update!");
    }
  } else {
    Serial.printf("HTTP OTA failed, code: %d\n", httpCode);
  }

  http.end();
}

void reportDeviceRequest() {
  if (WiFi.status() != WL_CONNECTED)
    return;

  HTTPClient http;
  WiFiClient client;
  String url = String("http://") + REPORT_URL + "/device_report?name=" + WIFIC_getDeviceName();

  http.begin(client, url);
  int httpCode = http.GET();

  if (httpCode > 0) {
    String response = http.getString();
    response.trim();
    Serial.print("RX:");
    Serial.println(response);

    if (response.startsWith("{")) {
      StaticJsonDocument<256> doc;
      if (deserializeJson(doc, response) == DeserializationError::Ok) {
        const char* cmd = doc["command"];
        if (cmd) {
          if (strcmp(cmd, "unlock") == 0) {
            int relay_id = doc["relay_id"] | 0;
            PINCTRL_trigger(relay_id);
          } else if (strcmp(cmd, "update") == 0) {
            const char* fw_path = doc["firmware"];
            if (fw_path && strlen(fw_path) > 0) {
              String fwUrl = String("http://") + REPORT_URL + String(fw_path);
              performOtaUpdate(fwUrl);
            }
          } else if (strcmp(cmd, "restart") == 0) {
            Serial.println("Restart command received.");
            ESP.restart();
          }
        }
      }
    }
  } else {
    Serial.printf("HTTP GET failed, error: %s\n", http.errorToString(httpCode).c_str());
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
