/* 
 *  Author: Rada Berar
 *  email: ujagaga@gmail.com
 *  
 *  WiFi connection module. 
 */
#include <WiFi.h>
#include <EEPROM.h>
#include <lwip/init.h>
#include <lwip/dns.h>
#include <lwip/ip_addr.h>
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

  // Force DHCP + custom DNS
  WiFi.config(INADDR_NONE, INADDR_NONE, INADDR_NONE, dns);

  WiFi.begin(st_ssid, st_pass);

  int i = 30;
  while ((i > 0) && (WiFi.status() != WL_CONNECTED)) {
    delay(1000);
    Serial.print(".");
    i--;
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    stationIP = WiFi.localIP();
    IPAddress gateway = WiFi.gatewayIP();

    Serial.printf("IP address: %s, gateway: %s\n",
                  stationIP.toString().c_str(), gateway.toString().c_str());
    apMode = false;
  } else {
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
  static unsigned long lastScanTime = 0;
  const unsigned long scanInterval = 5000; // 5 seconds

  if (apMode) {
    unsigned long now = millis();

    // If timeout expired or we’re ready for a retry
    if ((now - apModeAttempTime) > (AP_MODE_TIMEOUT_S * 1000) && 
        (now - lastScanTime) > scanInterval) {

      // Reset periodic scan timer
      lastScanTime = now;

      if (WiFi.softAPgetStationNum() > 0) {
        Serial.println("Clients connected — AP mode continues.");        
        return;
      }

      Serial.println("No clients — scanning for known SSID...");

      String ssidString = String(st_ssid);
      String apList = WIFIC_getApList();
      Serial.println(apList);

      if (apList.indexOf(ssidString) != -1) {
        apModeAttempTime = now; // reset main AP timeout
        Serial.printf("Found saved SSID '%s', switching to STA mode...\n", ssidString.c_str());
        WIFIC_stationMode();
      } else {
        Serial.printf("Saved SSID '%s' not found, will retry in 5 seconds.\n", ssidString.c_str());
      }
    }
  }
}
