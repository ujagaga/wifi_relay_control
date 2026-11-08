#ifndef CONFIG_H
#define CONFIG_H

#ifndef FW_VERSION
#define FW_VERSION              0       // Set to the GitHub Actions run number by CI builds.
#endif

#define DIAG_HOST               "debug.ujagaga.in.rs"   // nginx on the Oracle instance, proxies to the diag server on 127.0.0.1:8090.
#define DIAG_PORT               80
#define REPORT_HOST             "shtef.radinaradionica.com"   // Same server the relay devices report to.

#define PORTAL_PASS             "12345678"  // Password of the setup AP "WiFiDiag_XXXX".
#define PORTAL_TIMEOUT_MS       (5 * 60 * 1000ul)   // Reboot and retry home WiFi after this.

#define RELAY_AP_NAME           "Shtef_diag"    // Used by "apsta" tests to mimic the relay firmware softAP.
#define RELAY_AP_PASS           "abc121212"

#define REPEATER_AP_IP          IPAddress(192, 168, 44, 1)
#define NAPT_MAX                256     // NAT table entries for repeater mode.
#define NAPT_PORT_MAX           32

#define CONNECT_TIMEOUT_MS      30000
#define POLL_INTERVAL_MS        5000
#define MONITOR_INTERVAL_MS     15000
#define TCP_TIMEOUT_MS          5000
#define HTTP_TIMEOUT_MS         8000
#define DNS_TIMEOUT_MS          5000
#define LOG_MAX                 16000   // Log buffer kept in RAM until uploaded.

#endif
