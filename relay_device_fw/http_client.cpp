/* 
 *  Author: Rada Berar
 *  email: ujagaga@gmail.com
 */
#include <ESP8266WiFi.h>
#include "config.h"
#include "wifi_connection.h"

static unsigned long lastConnectAtemptTime = 0;
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
    
    client.flush();
    // Read and discard response
    unsigned long timeout = millis();
    while (client.connected() && millis() - timeout < 5000) {
      while (client.available()) {
        client.read();
      }
    }

    client.stop();
    // Done — no response read
    Serial.println("Http request to '" + path + "' done.");    
    fail_count = 0;
  }else{
    Serial.println(String("Could not connect to ") + REPORT_URL);
    fail_count++;
    if(fail_count>3){
      // Restarting after 3 failed attempts
      ESP.restart();
    }
  }
  lastConnectAtemptTime = millis();
}

void HTTP_CLIENT_process()
{    
  if(((millis() - lastConnectAtemptTime) > (UPDATE_TIMEOUT  + random(1000))) || (lastConnectAtemptTime == 0)){
    fireAndForgetRequest();    
  } 
}

