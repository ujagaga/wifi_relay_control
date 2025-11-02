/* 
 *  Author: Rada Berar
 *  email: ujagaga@gmail.com
 */
#include <ESP8266WiFi.h>
#include <ArduinoJson.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266httpUpdate.h>
#include "config.h"
#include "wifi_connection.h"
#include "pinctrl.h"

static unsigned long lastConnectAtemptTime = 0;
static int fail_count = 0;

void reportDeviceRequest() {
  WiFiClient client;
  if (client.connect(REPORT_URL, 80)) {
    const char* deviceName = WIFIC_getDeviceName();
    String path = "/device_report?name=" + String(deviceName);

    // Send HTTP GET request
    client.print(String("GET ") + path + " HTTP/1.1\r\n" +
                 "Host: " + REPORT_URL + "\r\n" +
                 "Connection: close\r\n\r\n");
    client.flush();

    // --- Read full HTTP response into a String ---
    String response;
    unsigned long timeout = millis();
    bool headers_done = false;
    while (client.connected() && millis() - timeout < 1000) {
      while (client.available()) {
        String line = client.readStringUntil('\n');
        if (!headers_done) {
          // Skip headers
          if (line == "\r" || line.length() == 0) {
            headers_done = true;
          }
        } else {
          response += line;
        }
      }
    }
    client.stop();

    response.trim();
    Serial.println("RX:");
    Serial.println(response);

    // --- Parse response ---
    if (response.startsWith("{")) {
      StaticJsonDocument<256> doc;
      DeserializationError err = deserializeJson(doc, response);
      if (!err) {
        const char* cmd = doc["command"];
        if (cmd) {
          if (strcmp(cmd, "unlock") == 0) {
            int relay_id = doc["relay_id"] | 0;
            Serial.printf("Unlock command received for relay %d\n", relay_id);
            PINCTRL_trigger(relay_id);
          } else if (strcmp(cmd, "update") == 0) {
            const char* fw_path = doc["firmware"];
            if (fw_path && strlen(fw_path) > 0) {
              String url = "http://" + String(REPORT_URL) + String(fw_path);
              Serial.println("Starting OTA update from: " + url);

              WiFiClient updateClient;  // Required for ESP8266 core >= 3.x
              t_httpUpdate_return ret = ESPhttpUpdate.update(updateClient, url.c_str());

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
                  break;  // reboot happens automatically
              }
            }
          } else if (strcmp(cmd, "restart") == 0) {
            Serial.println("Restart command received.");
            ESP.restart();
          }
        }
      } else {
        Serial.println("JSON parse error.");
      }
    }

    fail_count = 0;
  } else {
    Serial.println(String("Could not connect to ") + REPORT_URL);
    fail_count++;
    if (fail_count > 3) {
      ESP.restart();
    }
  }

  lastConnectAtemptTime = millis();
}

void HTTP_CLIENT_process()
{    
  if(((millis() - lastConnectAtemptTime) > (UPDATE_TIMEOUT  + random(100))) || (lastConnectAtemptTime == 0)){
    reportDeviceRequest();    
  } 
}
