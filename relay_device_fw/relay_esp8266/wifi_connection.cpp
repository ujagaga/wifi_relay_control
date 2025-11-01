/* 
 *  Author: Rada Berar
 *  email: ujagaga@gmail.com
 *  
 *  WiFi connection module. 
 */
#include <ESP8266WiFi.h>
#include <ESP_EEPROM.h>
#include <lwip/init.h>
#include <lwip/dns.h>
#include <lwip/ip_addr.h>
#include <user_interface.h>
#include "config.h"

static char myApName[32] = {0};    /* Array to form AP name based on read MAC */
static char st_ssid[SSID_SIZE] = {0};    /* SSID to connect to */
static char st_pass[WIFI_PASS_SIZE];    /* Password for the requested SSID */
static unsigned long connectionTimeoutCheck = 0;
static IPAddress stationIP;
static IPAddress apIP(192, 168, 1, 1);
static bool apMode = false;
static uint32_t apModeAttempTime = 0;
static IPAddress dns(8,8,8,8);

static bool checkValidIp(IPAddress IP){
  /* check if they are all zero value */
  if((IP[0] == 0) && (IP[1] == 0) && (IP[2] == 0) && (IP[3] == 0)){
      return false;
  }

  /* Check that they are not all 0xff (defaut empty flash value) */
  if((IP[0] == 0xff) && (IP[1] == 0xff) && (IP[2] == 0xff) && (IP[3] == 0xff)){
      return false;
  }
    
  return true;
}

char* WIFIC_getDeviceName(void){
  return myApName;
}

IPAddress WIFIC_getApIp(void){
  return apIP;
}

bool WIFIC_isApMode(void){
  return apMode;
}

/* Returns wifi scan results */
String WIFIC_getApList(void){
  String result = "";
  // WiFi.scanNetworks will return the number of networks found
  int n = WiFi.scanNetworks(); 
  if (n >0){ 
    result = WiFi.SSID(0); 
    for (int i = 1; i < n; ++i)
    {      
      result += "|" + WiFi.SSID(i);  
    }
  }
  return result;
}

/* Initiates a local AP */
void WIFIC_APMode(void){ 
  String wifi_statusMessage; 
  Serial.println("\nStarting AP");  

  WiFi.mode(WIFI_AP);  
  WiFi.begin();
  
  String ApName = AP_NAME_PREFIX + WiFi.macAddress();
  ApName.toCharArray(myApName, ApName.length() + 1); 

  WiFi.softAPConfig(apIP, apIP, IPAddress(255, 255, 255, 0));
  
  if(WiFi.softAP(myApName, PASSWORD)){
    wifi_statusMessage = "Running in AP mode. SSID: " + String(myApName) + ", IP:" + apIP.toString();  
    apMode = true;    
  }else{
    wifi_statusMessage = "Failed to switch to AP mode.";
  }
  Serial.println(wifi_statusMessage);
  
  apModeAttempTime = millis();
}

void WIFIC_stationMode(void){   
  Serial.printf("\n\nTrying STA mode with [%s] and [%s]\r\n", st_ssid, st_pass);

  bool useStaticIp = checkValidIp(stationIP);
  if( useStaticIp ){    
    IPAddress subnet(255, 255, 255, 0);
    IPAddress gateway(stationIP[0], stationIP[1],stationIP[2], 1); 

    WiFi.config(stationIP, gateway, IPAddress(255, 255, 255, 0), dns);    
  }else{
    WiFi.config(0U, 0U, 0U);  // This disables static config.
  }

  WiFi.begin(st_ssid, st_pass); 

    /* set timeout to 30 seconds*/
  int i = 30;    
  while((i > 0) && (WiFi.status() != WL_CONNECTED)){
    delay(1000);
    ESP.wdtFeed();       
    i--;
    Serial.print(".");
  } 
  Serial.println("");  

  if(WiFi.status() == WL_CONNECTED){
    stationIP = WiFi.localIP();
    IPAddress gateway = WiFi.gatewayIP();
    // force dns server
    ip_addr_t dnsserver;
    IP4_ADDR(&dnsserver, dns[0], dns[1], dns[2], dns[3]);
    dns_setserver(0, &dnsserver);

    Serial.printf("IP address: %s, gateway: %s \n", stationIP.toString().c_str(), gateway.toString().c_str());
    apMode = false;    
  }else{    
    WIFIC_APMode();     
  }     
}

String WIFIC_getStSSID(void){
  return String(st_ssid);
}

void WIFIC_setStSSID(String new_ssid){
  EEPROM.begin(EEPROM_SIZE);
  
  uint16_t addr;
  
  for(addr = 0; addr < new_ssid.length(); addr++){    
    EEPROM.put(addr + SSID_EEPROM_ADDR, new_ssid[addr]);
    st_ssid[addr] = new_ssid[addr];
  }
  EEPROM.put(addr + SSID_EEPROM_ADDR, 0);  
  st_ssid[addr] = 0;
  
  EEPROM.commit();
}

String WIFIC_getStPass(void){
  return String(st_pass);
}

void WIFIC_setStPass(String new_pass){
  EEPROM.begin(EEPROM_SIZE);
  
  uint16_t addr;
  for(addr = 0; addr < new_pass.length(); addr++){   
    EEPROM.put(addr + WIFI_PASS_EEPROM_ADDR, new_pass[addr]);
    st_pass[addr] = new_pass[addr];
  }
  EEPROM.put(addr + WIFI_PASS_EEPROM_ADDR, 0);
  st_pass[addr] = 0;
    
  EEPROM.commit();
}

IPAddress WIFIC_getStIP(void){
  return stationIP;
}

void WIFIC_init(void){  
  ESP.wdtFeed();
   /* Read settings from EEPROM */
  EEPROM.begin(EEPROM_SIZE);
  uint16_t i = 0;
  
  do{
    EEPROM.get(i + WIFI_PASS_EEPROM_ADDR, st_pass[i]);
    if((st_pass[i] < 32) || (st_pass[i] > 126)){
      /* Non printable character */
      break;
    }
    i++;
  }while(i < WIFI_PASS_SIZE);
  st_pass[i] = 0;

  i = 0;
  do{
    EEPROM.get(i + SSID_EEPROM_ADDR, st_ssid[i]);
    if((st_ssid[i] < 32) || (st_ssid[i] > 126)){
      /* Non printable character */
      break;
    }
    i++;
  }while(i < SSID_SIZE);
  st_ssid[i] = 0;

  WIFIC_APMode();
}

void WIFIC_process(void) {
  if (apMode && 
      ((millis() - apModeAttempTime) > (AP_MODE_TIMEOUT_S * 1000)) && 
      (st_ssid[0] != 0)) {

    if (wifi_softap_get_station_num() > 0) {
      Serial.println("Clients connected — AP mode continues.");
      apModeAttempTime = millis(); // Reset timer
      return; // Stay in AP mode
    }

    Serial.println("No clients — checking for known SSID...");

    String ssidString = String(st_ssid);
    String apList = WIFIC_getApList();
    int index = apList.indexOf(ssidString);

    Serial.println(apList);

    if (index != -1) {
      WIFIC_stationMode();
    }

    apModeAttempTime = millis();
  }
}
