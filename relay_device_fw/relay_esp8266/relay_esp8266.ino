/* 
 *  Author: Rada Berar
 *  email: ujagaga@gmail.com
 *  
 *  This is the main sketch file. 
 *  It provides a periodic pooling of other services.
 */

#include "wifi_connection.h"
#include "config.h"
#include "pinctrl.h"
#include "ota.h"
#include "web_socket.h"
#include "http_server.h"
#include "http_client.h"
#include "mqtt_sub.h"


static String statusMessage = "";         /* This is set and requested from other modules. */

void MAIN_setStatusMsg(String msg){
  statusMessage = msg;
}

String MAIN_getStatusMsg(void){
  return statusMessage;
}

void setup(void) {
  /* Need to wait for background processes to complete. Otherwise trouble with gpio.*/
  delay(100);   
  Serial.begin(115200);  
  //ESP.eraseConfig();
  PINCTRL_init(); 
  WIFIC_init();
  WS_init();  
  HTTP_SERVER_init();
}

void loop(void) { 
  if(OTA_updateInProgress()){
    OTA_process();
  }else{
    if(WIFIC_isApMode()){
      HTTP_SERVER_process();
      WS_process();
    }else{
      HTTP_CLIENT_process();    
      MQTT_process();
    }   
    
    WIFIC_process();       
    PINCTRL_process();    
  } 
}
