#ifndef CONFIG_H
#define CONFIG_H

#define PASSWORD "abc121212"

#define AP_MODE_TIMEOUT_S                                                      \
  30 // After this period since startup, try to connect as wifi client. This is
     // to make sure router lease is updated.
#define TRIGGER_TIMEOUT 1000
#define RELAY_1_PIN                                                            \
  5 // Pin 16 is default and active on boot and triggeres a relay for about a
    // second. Use pin 5 to avoid this.
#define RELAY_2_PIN 14
#define RELAY_3_PIN 12
#define RELAY_4_PIN 13

#define UPDATE_TIMEOUT (30 * 1000ul)
#define REPORT_URL "vm120.ujagaga.in.rs" // E.G. "mywebsite.com" without http://

#define AP_NAME_PREFIX "Gate_sw_" // Will be appended by device MAC

#define WIFI_PASS_EEPROM_ADDR (0)
#define WIFI_PASS_SIZE (32)
#define SSID_EEPROM_ADDR (WIFI_PASS_EEPROM_ADDR + WIFI_PASS_SIZE)
#define SSID_SIZE (32)
#define EEPROM_SIZE (WIFI_PASS_SIZE + SSID_SIZE)

#define MQTT_URL "140.238.210.203"
#define MQTT_PORT 50000
#define MQTT_PASS "Dv@5es1ra"
#define MQTT_USER "ujagaga"
#define APP_NAME "VM120_Gate_Server"
#define MQTT_TOPIC_CMD APP_NAME "/command"

#endif
