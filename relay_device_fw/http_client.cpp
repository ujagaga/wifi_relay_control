/* 
 *  Author: Rada Berar
 *  email: ujagaga@gmail.com
 */
#include <ESP8266WiFi.h>
#include "config.h"
#include "wifi_connection.h"

static unsigned long lastConnectTime = 0;
static int fail_count = 0;

void fireAndForgetRequest() {
  WiFiClient client;
  if (client.connect(REPORT_URL, 80)) {
    // Get device name
    const char* deviceName = WIFIC_getDeviceName();

    // Form the path with query param
    String path = "/device_report?name=" + String(deviceName) + "&timestamp=" + String(millis());

    // Send HTTP GET request
    client.print(String("GET ") + path + " HTTP/1.1\r\n" +
                 "Host: " + REPORT_URL + "\r\n" + 
                 "Connection: close\r\n\r\n");
    // Done — no response read
    Serial.println("Http request to '" + path + "' done.");    
    fail_count = 0;
  }else{
    Serial.println(String("Could not connect to ") + REPORT_URL);
    fail_count++;
    if(fail_count>4){
      // Restarting after 5 failed attempts
      ESP.restart();
    }
  }
  lastConnectTime = millis();
}

void HTTP_CLIENT_process()
{  
  if((millis() - lastConnectTime) > UPDATE_TIMEOUT){
    fireAndForgetRequest();
  } 
}

