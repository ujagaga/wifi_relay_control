#ifndef WIFI_CONNECTION_H
#define WIFI_CONNECTION_H

#include <WiFiClient.h>


extern void WIFIC_init(void);
extern bool WIFIC_stationMode(void);
extern void WIFIC_APMode(void);
extern void WIFIC_setStSSID(String new_ssid);
extern void WIFIC_setStPass(String new_pass);
extern String WIFIC_getApList(void);
extern String WIFIC_getStSSID(void);
extern String WIFIC_getStPass(void);
extern char* WIFIC_getDeviceName(void);
extern void WIFIC_process(void);
extern bool WIFIC_isApMode(void);

#endif
