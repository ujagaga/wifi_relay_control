/* 
 *  Author: Rada Berar
 *  email: ujagaga@gmail.com
 *  
 *  GPIO management module
 */
#include "wifi_connection.h"
#include "config.h"


static int currentPinVal[4] = {0}; 
static int pin_num[4] = {RELAY_1_PIN, RELAY_2_PIN, RELAY_3_PIN, RELAY_4_PIN};
static uint32_t PinWriteTimestamp[4] = {0};

void PINCTRL_init(){
  pinMode(pin_num[0], OUTPUT);
  pinMode(pin_num[1], OUTPUT);
  pinMode(pin_num[2], OUTPUT);
  pinMode(pin_num[3], OUTPUT);
}

void PINCTRL_trigger(int id)
{  
  if((id < 0) || (id > 3)){
    return;
  }

  if((millis() - PinWriteTimestamp[id]) < TRIGGER_TIMEOUT){
    return;
  }  

  Serial.printf("SW ON:%d\r\n", id);
  digitalWrite(pin_num[id], HIGH);
  PinWriteTimestamp[id] = millis();
}

void PINCTRL_process(){
  for(int i = 0; i < 4; ++i){
    if((millis() - PinWriteTimestamp[i]) > TRIGGER_TIMEOUT){
      if(PinWriteTimestamp[i] > 0){
        digitalWrite(pin_num[i], LOW);
        PinWriteTimestamp[i] = 0;
        
        Serial.printf("SW OFF:%d\r\n", i);
      }      
    }
  }
}
