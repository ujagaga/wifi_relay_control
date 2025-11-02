#ifndef CONFIG_H
#define CONFIG_H

#define PASSWORD                "abc121212"

#define AP_MODE_TIMEOUT_S       30 // After this period since startup, try to connect as wifi client. This is to make sure router lease is updated.
#define TRIGGER_TIMEOUT         1000

#define RELAY_1_PIN             5   // Pin 16 is default and active on boot and triggeres a relay for about a second. Use pin 5 to avoid this.   
#define RELAY_2_PIN             14   
#define RELAY_3_PIN             12   
#define RELAY_4_PIN             13

// 5 minutes to start the OTA update. If not, stop the service.
#define UPDATE_TIMEOUT          (2000ul)
#define REPORT_URL              "reverse_http_tunnel_http.url" // E.G. "mywebsite.com" without http://

#define AP_NAME_PREFIX          "Gate_sw_" // Will be appended by device MAC

#define WIFI_PASS_EEPROM_ADDR   (0)
#define WIFI_PASS_SIZE          (32)
#define SSID_EEPROM_ADDR        (WIFI_PASS_EEPROM_ADDR + WIFI_PASS_SIZE)
#define SSID_SIZE               (32)
#define EEPROM_SIZE             (WIFI_PASS_SIZE + SSID_SIZE)   

#endif
