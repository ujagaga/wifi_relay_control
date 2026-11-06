/*
 *  Author: Rada Berar
 *  email: ujagaga@gmail.com
 *
 *  WiFi diagnostic firmware for a Wemos D1 mini.
 *  Connects to a "home" network (phone hotspot or a router that works), polls the
 *  diag server for commands, runs connectivity tests on another network (the repeater),
 *  returns home and uploads the log. Firmware can be replaced remotely (e.g. from a GitHub release).
 *  See README.md for commands.
 */
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266httpUpdate.h>
#include <WiFiClientSecureBearSSL.h>
#include <DNSServer.h>
#include <EEPROM.h>
#include <ArduinoJson.h>
#include <lwip/dns.h>
#include "config.h"
#if __has_include("secrets.h")
#include "secrets.h"    /* Optional, not in git: DEFAULT_HOME_SSID / DEFAULT_HOME_PASS. */
#endif

#define CREDS_MAGIC   0xD1A60002

struct Creds {
  uint32_t magic;
  uint32_t defaultsHash;  /* Hash of the built-in defaults last written, so they are applied once per build. */
  char ssid[33];
  char pass[65];
};

static Creds home;
static uint8_t staMac[6];
static String devId;
static String logBuf;
static bool logTruncated = false;

static ESP8266WebServer web(80);
static DNSServer dnsServer;
static bool portalMode = false;
static uint32_t portalStart = 0;
static uint32_t lastPoll = 0;

static WiFiEventHandler discHandler, assocHandler;
static volatile uint16_t discCount = 0;
static volatile uint8_t discReason = 0;
static volatile uint16_t assocCount = 0;
static uint16_t loggedDisc = 0, loggedAssoc = 0;

static void logf(const char* fmt, ...) {
  char line[300];
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(line, sizeof(line), fmt, ap);
  va_end(ap);

  char ts[16];
  snprintf(ts, sizeof(ts), "[%6lu] ", millis() / 1000);
  Serial.print(ts);
  Serial.println(line);

  if (logBuf.length() + strlen(line) < LOG_MAX) {
    logBuf += ts;
    logBuf += line;
    logBuf += '\n';
  } else if (!logTruncated) {
    logBuf += "...log full, lines dropped\n";
    logTruncated = true;
  }
}

/* WiFi events arrive in SDK context, so only count them there and log from the main loop. */
static void logWifiEvents() {
  if (assocCount != loggedAssoc) {
    loggedAssoc = assocCount;
    logf("  associated with %s ch %d", WiFi.BSSIDstr().c_str(), WiFi.channel());
  }
  if (discCount != loggedDisc) {
    logf("  disconnected, last reason %d (%u events)", discReason, (unsigned)(discCount - loggedDisc));
    loggedDisc = discCount;
  }
}

static bool parseMac(const char* s, uint8_t* mac) {
  unsigned int b[6];
  if (sscanf(s, "%x:%x:%x:%x:%x:%x", &b[0], &b[1], &b[2], &b[3], &b[4], &b[5]) != 6) return false;
  for (int i = 0; i < 6; i++) mac[i] = b[i];
  return true;
}

static String diagUrl(const char* path) {
  return String("http://") + DIAG_HOST + ":" + DIAG_PORT + path;
}

static bool connectTo(const char* ssid, const char* pass, const uint8_t* bssid, const uint8_t* mac) {
  WiFi.disconnect();
  delay(100);
  wifi_set_macaddr(STATION_IF, (uint8_t*)mac);
  logf("Connecting to '%s' as %s%s", ssid, WiFi.macAddress().c_str(), bssid ? " (fixed BSSID)" : "");
  WiFi.begin(ssid, pass, 0, bssid);

  uint32_t start = millis();
  int last = -1;
  while (millis() - start < CONNECT_TIMEOUT_MS) {
    logWifiEvents();
    int s = WiFi.status();
    if (s != last) {
      logf("  status %d after %lums", s, millis() - start);
      last = s;
    }
    if (s == WL_CONNECTED) return true;
    delay(100);
  }
  logWifiEvents();
  logf("  connect timeout, status %d", WiFi.status());
  return false;
}

static bool connectHome() {
  return connectTo(home.ssid, home.pass, nullptr, staMac);
}

static void scanNetworks() {
  int n = WiFi.scanNetworks(false, true);
  logf("Scan: %d networks (enc: 2=TKIP 4=CCMP 5=WEP 7=open 8=auto)", n);
  for (int i = 0; i < n; i++) {
    logf("  %-32s %s ch %2d %4d dBm enc %d%s", WiFi.SSID(i).c_str(), WiFi.BSSIDstr(i).c_str(),
         WiFi.channel(i), WiFi.RSSI(i), WiFi.encryptionType(i), WiFi.isHidden(i) ? " hidden" : "");
  }
  WiFi.scanDelete();
}

static void tcpProbe(const char* label, IPAddress ip, uint16_t port) {
  WiFiClient client;
  client.setTimeout(TCP_TIMEOUT_MS);
  uint32_t t = millis();
  bool ok = client.connect(ip, port);
  logf("TCP %s (%s:%u) -> %s, %lums", label, ip.toString().c_str(), port, ok ? "OK" : "FAILED", millis() - t);
  client.stop();
}

static bool dnsProbe(const char* host, IPAddress& ip) {
  uint32_t t = millis();
  bool ok = WiFi.hostByName(host, ip, DNS_TIMEOUT_MS) == 1;
  logf("DNS %s via %s -> %s, %lums", host, WiFi.dnsIP(0).toString().c_str(),
       ok ? ip.toString().c_str() : "FAILED", millis() - t);
  return ok;
}

static void httpProbe(const String& url) {
  WiFiClient client;
  HTTPClient http;
  http.setTimeout(HTTP_TIMEOUT_MS);
  uint32_t t = millis();
  if (!http.begin(client, url)) {
    logf("HTTP %s -> bad url", url.c_str());
    return;
  }
  int code = http.GET();
  int len = (code > 0) ? http.getString().length() : 0;
  logf("HTTP %s -> %d %s, %d bytes, %lums", url.c_str(), code,
       code > 0 ? "" : http.errorToString(code).c_str(), len, millis() - t);
  http.end();
}

/* Checks each hop from the local network to the relay server on the current connection. */
static void runProbes() {
  IPAddress local = WiFi.localIP();
  IPAddress gw = WiFi.gatewayIP();
  logf("IP %s mask %s gw %s dns %s %s", local.toString().c_str(), WiFi.subnetMask().toString().c_str(),
       gw.toString().c_str(), WiFi.dnsIP(0).toString().c_str(), WiFi.dnsIP(1).toString().c_str());
  logf("BSSID %s ch %d RSSI %d dBm, free heap %u", WiFi.BSSIDstr().c_str(), WiFi.channel(), WiFi.RSSI(), ESP.getFreeHeap());
  if (local[0] == 192 && local[1] == 168 && local[2] == 4) {
    logf("WARNING: network uses 192.168.4.x, same as the relay firmware softAP");
  }

  tcpProbe("gateway:80", gw, 80);
  tcpProbe("gateway:53", gw, 53);
  tcpProbe("1.1.1.1:80", IPAddress(1, 1, 1, 1), 80);
  tcpProbe("8.8.8.8:53", IPAddress(8, 8, 8, 8), 53);
  IPAddress diagIp;
  if (dnsProbe(DIAG_HOST, diagIp)) {
    tcpProbe("diag server", diagIp, DIAG_PORT);
  }

  IPAddress reportIp;
  if (dnsProbe(REPORT_HOST, reportIp)) {
    tcpProbe(REPORT_HOST ":80", reportIp, 80);
  }
  httpProbe(String("http://") + REPORT_HOST + "/");
  httpProbe("http://connectivitycheck.gstatic.com/generate_204");
  httpProbe(diagUrl("/diag/ping"));
  httpProbe(diagUrl("/diag/blob?size=8000"));   // Larger response, exposes MTU/fragmentation problems.

  /* The relay firmware falls back to public DNS when DHCP provided DNS fails. Check that path too. */
  dns_setserver(0, IPAddress(8, 8, 8, 8));
  dns_setserver(1, IPAddress(1, 1, 1, 1));
  dnsProbe(REPORT_HOST, reportIp);
  httpProbe(String("http://") + REPORT_HOST + "/");
}

/* Stays on the network and checks periodically, in case access stops after a while. */
static void monitor(uint32_t minutes) {
  uint32_t start = millis();
  while (millis() - start < minutes * 60000ul) {
    uint32_t t = millis();
    while (millis() - t < MONITOR_INTERVAL_MS) {
      logWifiEvents();
      delay(100);
    }
    if (WiFi.status() == WL_CONNECTED) {
      logf("RSSI %d dBm", WiFi.RSSI());
      httpProbe(String("http://") + REPORT_HOST + "/");
      httpProbe(diagUrl("/diag/ping"));
    } else {
      logf("not connected, status %d", WiFi.status());
    }
  }
}

static void uploadLog() {
  if (logBuf.length() == 0 || WiFi.status() != WL_CONNECTED) return;

  WiFiClient client;
  HTTPClient http;
  http.setTimeout(HTTP_TIMEOUT_MS);
  http.begin(client, diagUrl("/diag/log?id=") + devId);
  http.addHeader("Content-Type", "text/plain");
  int code = http.POST(logBuf);
  http.end();
  if (code == 200) {
    logBuf = "";
    logTruncated = false;
  } else {
    Serial.printf("Log upload failed: %d\n", code);
  }
}

static void runTest(JsonDocument& doc) {
  const char* ssid = doc["ssid"] | "";
  const char* pass = doc["pass"] | "";
  const char* bssidStr = doc["bssid"] | "";
  const char* macStr = doc["mac"] | "";
  bool apsta = doc["apsta"] | false;
  uint32_t minutes = doc["minutes"] | 0;
  uint8_t bssid[6], mac[6];
  bool useBssid = parseMac(bssidStr, bssid);
  bool useMac = parseMac(macStr, mac);

  logf("=== TEST ssid='%s' bssid=%s mac=%s apsta=%d minutes=%u", ssid, bssidStr, macStr, apsta, minutes);
  scanNetworks();
  uploadLog();  /* In case we never make it back. */

  if (apsta) {
    WiFi.mode(WIFI_AP_STA);
    WiFi.softAPConfig(IPAddress(192, 168, 4, 1), IPAddress(192, 168, 4, 1), IPAddress(255, 255, 255, 0));
    WiFi.softAP(RELAY_AP_NAME, RELAY_AP_PASS);
  }
  if (connectTo(ssid, pass, useBssid ? bssid : nullptr, useMac ? mac : staMac)) {
    runProbes();
    monitor(minutes);
  }
  if (apsta) {
    WiFi.softAPdisconnect(true);
    WiFi.mode(WIFI_STA);
  }
  logf("=== TEST end, returning home");
  connectHome();  /* If this fails loop() restarts the device. */
}

static void doUpdate(const char* url) {
  logf("OTA from %s, free heap %u", url, ESP.getFreeHeap());
  uploadLog();

  ESPhttpUpdate.setFollowRedirects(HTTPC_FORCE_FOLLOW_REDIRECTS);  /* GitHub release links redirect. */
  t_httpUpdate_return ret;
  if (strncmp(url, "https://", 8) == 0) {
    BearSSL::WiFiClientSecure client;
    client.setInsecure();
    ret = ESPhttpUpdate.update(client, url);
  } else {
    WiFiClient client;
    ret = ESPhttpUpdate.update(client, url);
  }
  /* On success the device reboots inside update(). */
  logf("OTA failed, ret %d, error (%d): %s", ret, ESPhttpUpdate.getLastError(), ESPhttpUpdate.getLastErrorString().c_str());
}

static void handleCommand(const String& body) {
  JsonDocument doc;
  if (deserializeJson(doc, body)) {
    logf("Bad command: %s", body.c_str());
    return;
  }
  const char* cmd = doc["cmd"] | "";
  if (!*cmd) return;

  logf("Command: %s", body.c_str());
  if (strcmp(cmd, "test") == 0) {
    runTest(doc);
  } else if (strcmp(cmd, "scan") == 0) {
    scanNetworks();
  } else if (strcmp(cmd, "probe") == 0) {
    runProbes();
  } else if (strcmp(cmd, "update") == 0) {
    doUpdate(doc["url"] | "");
  } else if (strcmp(cmd, "reboot") == 0) {
    uploadLog();
    ESP.restart();
  } else {
    logf("Unknown command");
  }
  uploadLog();
}

static void poll() {
  WiFiClient client;
  HTTPClient http;
  http.setTimeout(HTTP_TIMEOUT_MS);
  String url = diagUrl("/diag/poll?id=") + devId + "&fw=" + FW_VERSION + "&rssi=" + WiFi.RSSI() +
               "&ip=" + WiFi.localIP().toString();
  http.begin(client, url);
  int code = http.GET();
  String body = (code == 200) ? http.getString() : "";
  http.end();

  if (code != 200) {
    Serial.printf("Poll failed: %d %s\n", code, http.errorToString(code).c_str());
    return;
  }
  handleCommand(body);
}

static void saveHome(const char* ssid, const char* pass, uint32_t defaultsHash) {
  memset(&home, 0, sizeof(home));
  home.magic = CREDS_MAGIC;
  home.defaultsHash = defaultsHash;
  strncpy(home.ssid, ssid, sizeof(home.ssid) - 1);
  strncpy(home.pass, pass, sizeof(home.pass) - 1);
  EEPROM.put(0, home);
  EEPROM.commit();
}

static void startPortal() {
  /* Scan first, so the page can offer the visible networks. */
  int n = WiFi.scanNetworks();
  String options;
  for (int i = 0; i < n; i++) {
    options += "<option value=\"" + WiFi.SSID(i) + "\">";
  }
  WiFi.scanDelete();

  String apName = "WiFiDiag_" + devId.substring(devId.length() - 4);
  WiFi.mode(WIFI_AP);
  WiFi.softAP(apName.c_str(), PORTAL_PASS);
  dnsServer.start(53, "*", WiFi.softAPIP());  /* Captive portal: every name resolves to us. */

  static String page;
  page = "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width'><title>WiFi diag</title></head>"
         "<body style='font-family:sans-serif'><h3>WiFi diag " + devId + "</h3>"
         "<p>Enter a WiFi network with working internet (e.g. phone hotspot).</p>"
         "<form method='post' action='/save'>SSID<br><input name='ssid' list='nets' maxlength='32'><datalist id='nets'>" +
         options + "</datalist><br>Password<br><input name='pass' type='password' maxlength='64'><br><br>"
         "<input type='submit' value='Save'></form></body></html>";

  web.on("/save", HTTP_POST, []() {
    saveHome(web.arg("ssid").c_str(), web.arg("pass").c_str(), home.defaultsHash);
    web.send(200, "text/plain", "Saved. Restarting and connecting to " + web.arg("ssid"));
    delay(500);
    ESP.restart();
  });
  web.onNotFound([]() { web.send(200, "text/html", page); });
  web.begin();

  portalMode = true;
  portalStart = millis();
  logf("Setup portal: join WiFi '%s' password '%s', open http://192.168.4.1", apName.c_str(), PORTAL_PASS);
}

void setup() {
  Serial.begin(115200);
  delay(200);

  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.macAddress(staMac);
  devId = "D1DIAG_" + WiFi.macAddress();
  devId.replace(":", "");

  discHandler = WiFi.onStationModeDisconnected([](const WiFiEventStationModeDisconnected& e) {
    discReason = e.reason;
    discCount++;
  });
  assocHandler = WiFi.onStationModeConnected([](const WiFiEventStationModeConnected& e) {
    assocCount++;
  });

  logf("WiFi diag fw %d, id %s, reset reason: %s", FW_VERSION, devId.c_str(), ESP.getResetReason().c_str());

  EEPROM.begin(sizeof(Creds));
  EEPROM.get(0, home);
  if (home.magic != CREDS_MAGIC) memset(&home, 0, sizeof(home));
#ifdef DEFAULT_HOME_SSID
  /* FNV-1a of the defaults. A new USB build with other defaults applies them once; portal changes survive reboots. */
  uint32_t h = 2166136261u;
  for (const char* s = DEFAULT_HOME_SSID "\n" DEFAULT_HOME_PASS; *s; s++) h = (h ^ (uint8_t)*s) * 16777619u;
  if (home.defaultsHash != h) {
    saveHome(DEFAULT_HOME_SSID, DEFAULT_HOME_PASS, h);
    logf("Home WiFi set to built-in default '%s'", DEFAULT_HOME_SSID);
  }
#endif
  if (home.magic != CREDS_MAGIC) {
    logf("No home WiFi configured");
    startPortal();
  } else if (!connectHome()) {
    logf("Home WiFi '%s' not available", home.ssid);
    startPortal();
  } else {
    runProbes();  /* Shows on serial even if the diag server is unreachable from here. */
  }
}

void loop() {
  if (portalMode) {
    dnsServer.processNextRequest();
    web.handleClient();
    if (millis() - portalStart > PORTAL_TIMEOUT_MS) ESP.restart();
    return;
  }

  if (WiFi.status() != WL_CONNECTED) {
    logf("Home WiFi lost");
    if (!connectHome()) ESP.restart();
  }

  if (millis() - lastPoll > POLL_INTERVAL_MS) {
    uploadLog();
    poll();
    lastPoll = millis();
  }
}
