/* 
 *  Author: Rada Berar
 *  email: ujagaga@gmail.com
 *  
 *  GPIO management module
 */
#include "wifi_connection.h"
#include "config.h"


static int currentPinVal[2] = {0}; 
static int pin_num[] = {RELAY_1_PIN, RELAY_2_PIN};
static uint32_t PinWriteTimestamp[4] = {0};

void PINCTRL_init(){
  pinMode(pin_num[0], OUTPUT);
  pinMode(pin_num[1], OUTPUT);
}

void PINCTRL_trigger(int id)
{  
  if((id < 0) || (id > 1)){
    return;
  }

  if((millis() - PinWriteTimestamp[id]) < (UPDATE_TIMEOUT * 2)){
    return;
  }  

  Serial.printf("SW ON:%d\r\n", id);
  digitalWrite(pin_num[id], HIGH);
  PinWriteTimestamp[id] = millis();
}

void PINCTRL_process(){
  if((millis() - PinWriteTimestamp[0]) > (RESET_TIMEOUT_S * 1000)){
    if(PinWriteTimestamp[0] > 0){
      digitalWrite(pin_num[0], LOW);
      PinWriteTimestamp[0] = 0;
      
      Serial.printf("SW OFF:0\r\n");
      ESP.restart();
    }      
  }

  if((millis() - PinWriteTimestamp[1]) > (TRIGGER_TIMEOUT_S * 1000)){
    if(PinWriteTimestamp[1] > 0){
      digitalWrite(pin_num[1], LOW);
      PinWriteTimestamp[1] = 0;
      
      Serial.printf("SW OFF:1\r\n");
    }      
  }
}
