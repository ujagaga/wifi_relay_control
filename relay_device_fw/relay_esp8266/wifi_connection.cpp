/* 
 *  Author: Rada Berar
 *  email: ujagaga@gmail.com
 *  
 *  WiFi connection module. 
 */
#include <ESP8266WiFi.h>
#include <ESP_EEPROM.h>
#include <lwip/dns.h>
#include "config.h"

static char myApName[32] = {0};    /* Array to form AP name based on read MAC */
static char st_ssid[SSID_SIZE] = {0};    /* SSID to connect to */
static char st_pass[WIFI_PASS_SIZE];    /* Password for the requested SSID */
static IPAddress stationIP;
static IPAddress apIP(192, 168, 4, 1);
static bool apMode = false;
static uint32_t apModeAttempTime = 0;
static bool staConnecting = false;
static uint32_t staConnectStartTime = 0;

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

static void startSoftAP(void){
  String ApName = AP_NAME_PREFIX + WiFi.macAddress();
  ApName.toCharArray(myApName, ApName.length() + 1); 

  WiFi.softAPConfig(apIP, apIP, IPAddress(255, 255, 255, 0));
  
  if(WiFi.softAP(myApName, PASSWORD)){
    Serial.println("AP running. SSID: " + String(myApName) + ", IP:" + apIP.toString());
    apMode = true;    
  }else{
    Serial.println("Failed to start AP.");
  }
}

/* Initiates a local AP only */
void WIFIC_APMode(void){ 
  Serial.println("\nStarting AP mode");  

  WiFi.mode(WIFI_AP);  
  startSoftAP();

  staConnecting = false;
  apModeAttempTime = millis();
}

/* Keeps the AP running and starts a non blocking STA connection attempt. */
void WIFIC_stationMode(void){
  Serial.printf("\n\nTrying STA+AP mode with [%s] and [%s]\r\n", st_ssid, st_pass);
  
  WiFi.setAutoReconnect(true);
  WiFi.mode(WIFI_AP_STA);
  startSoftAP();
  WiFi.config(0U, 0U, 0U);  // This disables static config.
  WiFi.begin(st_ssid, st_pass); 

  staConnecting = true;
  staConnectStartTime = millis();
}

/* Replace DHCP provided DNS (e.g. an unreliable repeater) with public DNS servers. */
void WIFIC_useFallbackDns(void){
  IPAddress dns1(8, 8, 8, 8);
  IPAddress dns2(1, 1, 1, 1);
  dns_setserver(0, dns1);
  dns_setserver(1, dns2);
  Serial.println("Switched to fallback DNS 8.8.8.8, 1.1.1.1");
}

static void onStationConnected(void){
  stationIP = WiFi.localIP();
  IPAddress gateway = WiFi.gatewayIP();
  IPAddress primaryDns = WiFi.dnsIP(0);
  IPAddress secondaryDns = WiFi.dnsIP(1);

  Serial.printf("IP address: %s, gateway: %s, DNS: %s, %s\n",
                stationIP.toString().c_str(), gateway.toString().c_str(),
                primaryDns.toString().c_str(), secondaryDns.toString().c_str());

  IPAddress endpointIP;
  if (WiFi.hostByName(REPORT_URL, endpointIP, 5000) == 1) {
    Serial.printf("Resolved %s to %s\n", REPORT_URL, endpointIP.toString().c_str());
  } else {
    Serial.printf("DNS lookup failed for %s; using fallback DNS.\n", REPORT_URL);
    WIFIC_useFallbackDns();
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
  }while(i < (WIFI_PASS_SIZE - 1));
  st_pass[i] = 0;

  i = 0;
  do{
    EEPROM.get(i + SSID_EEPROM_ADDR, st_ssid[i]);
    if((st_ssid[i] < 32) || (st_ssid[i] > 126)){
      /* Non printable character */
      break;
    }
    i++;
  }while(i < (SSID_SIZE - 1));
  st_ssid[i] = 0;

  WiFi.persistent(false);   /* Do not use or overwrite credentials stored in SDK flash. */
  WIFIC_APMode();
}

void WIFIC_process(void) {
  uint32_t now = millis();

  if (staConnecting) {
    if (WiFi.status() == WL_CONNECTED) {
      staConnecting = false;
      onStationConnected();
    } else if ((now - staConnectStartTime) > (STA_CONNECT_TIMEOUT_S * 1000ul)) {
      Serial.println("STA connection failed, falling back to AP only.");
      WIFIC_APMode();
    }
    return;
  }

  if (apMode) {
    if (WiFi.status() == WL_CONNECTED) {
      /* STA+AP connected. Drop the AP once nobody uses it. */
      if (wifi_softap_get_station_num() == 0) {
        Serial.println("No AP clients, switching to STA mode only.");
        WiFi.mode(WIFI_STA);
        apMode = false;
      }
    } else if ((strlen(st_ssid) > 0) && ((now - apModeAttempTime) > (AP_MODE_TIMEOUT_S * 1000ul))) {
      WIFIC_stationMode();
    }
    return;
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi connection lost, reconnecting in STA+AP mode...");
    WIFIC_stationMode();
  }
}
