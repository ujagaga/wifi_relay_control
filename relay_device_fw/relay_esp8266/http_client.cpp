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
  if (WiFi.status() != WL_CONNECTED) return;

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
              Serial.println("Starting OTA update from: " + fwUrl);

              WiFiClient updateClient;  // must be a named variable, not temporary
              t_httpUpdate_return ret = ESPhttpUpdate.update(updateClient, fwUrl);

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
          }else if (strcmp(cmd, "restart") == 0) {
            Serial.println("Restart command received.");
            PINCTRL_trigger(0);
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


void HTTP_CLIENT_process()
{    
  if(((millis() - lastConnectAtemptTime) > (UPDATE_TIMEOUT  + random(100))) || (lastConnectAtemptTime == 0)){
    reportDeviceRequest();    
  } 
}
