# WiFi diag firmware (Wemos D1 mini)

Remote diagnostic tool to find out why ESP8266 relay devices lose server access behind the client's repeater.

The D1 mini joins a **home** network that has working internet, such as a phone hotspot or a router that works. It polls the diag server for commands every 5 s, and when told to it:
- joins another network (the repeater) and checks every hop from the gateway to `shtef.radinaradionica.com`,
- returns to the home network and uploads the log.

Everything is also printed on the serial port (115200 baud), so the client can paste the Serial Monitor output if the diag server can't be reached at all.

## Build and flash (here, before shipping)

```
arduino-cli compile --fqbn esp8266:esp8266:d1_mini --output-dir build .
arduino-cli upload --fqbn esp8266:esp8266:d1_mini -p /dev/ttyUSB0 --input-dir build .
```
In the Arduino IDE, select the board "LOLIN(WEMOS) D1 R2 & mini". The only library you need is ArduinoJson.

To ship the device with the client's home WiFi built in (no setup needed, just plug it in), create `secrets.h` next to `config.h`. It is gitignored, because the repo and the release binaries are public:
```
#define DEFAULT_HOME_SSID       "ClientHotspot"
#define DEFAULT_HOME_PASS       "password"
```
A USB flash with new defaults writes them to EEPROM on first boot. After that, networks saved through the setup page and OTA builds from CI (which have no `secrets.h`) keep the stored credentials.

## Client setup

1. Power the D1 mini from USB, either a PC or a phone charger.
2. On a phone, join WiFi `WiFiDiag_XXXX` with password `12345678`. The setup page should open by itself. If it doesn't, open http://192.168.4.1.
3. Enter a WiFi network with working internet, then press Save.

If that network can't be reached, the setup AP comes back. It stays up for 5 minutes, then the device reboots and tries again.

## Diag server

Deploy `server/diag_server.py` on the Oracle instance. It only needs Python 3 and its standard library:
```
python3 diag_server.py 8090
```
It runs as the systemd service `wifi_diag` from `~/wifi_diag_server`. The OCI security list blocks 8090, so nginx proxies `http://debug.ujagaga.in.rs` (port 80) to `127.0.0.1:8090` (`/etc/nginx/sites-available/debug.ujagaga.in.rs.conf`). The firmware uses `DIAG_HOST`/`DIAG_PORT` from `config.h`.

- `logs/<id>.seen` is updated on every poll: time, public IP, fw version, RSSI, local IP.
- `logs/<id>.log` collects the uploaded logs.
- To queue a command, write `cmd/<id>.json`. It is delivered once, then renamed to `.sent`.

The device id is `D1DIAG_<MAC>` and is shown on the setup page and in the serial log.

## Commands

| JSON | Action |
| --- | --- |
| `{"cmd":"scan"}` | List visible networks: SSID, BSSID, channel, RSSI, encryption |
| `{"cmd":"probe"}` | Run the connectivity checks on the home network |
| `{"cmd":"test","ssid":"Repeater","pass":"..."}` | Join the network, run the checks, return home, upload the log |
| `{"cmd":"update","url":"https://github.com/ujagaga/wifi_relay_control/releases/download/diag-fw/wifi_diag_d1mini.bin"}` | OTA update over http or https; GitHub redirects are followed |
| `{"cmd":"reboot"}` | Restart |

Optional fields for `test`:
- `"bssid":"AA:BB:CC:DD:EE:FF"`: join this exact AP, for when the router and repeater share an SSID.
- `"mac":"C4:D8:D5:34:D3:46"`: use a relay device's MAC, to test MAC filtering or blocking on the router. Don't do this while that device is connected to the same network.
- `"apsta":true`: run the relay firmware's softAP (192.168.4.1) during the test, like the relay firmware in AP+STA mode does.
- `"minutes":N`: stay connected and recheck every 15 s, for when access stops after a while.

The checks: DHCP result, TCP to gateway:80/53, 1.1.1.1:80, 8.8.8.8:53; DNS and TCP for the diag server; DNS for `REPORT_HOST`; HTTP to `REPORT_HOST`, Google generate_204, diag ping, an 8 KB download; then DNS and HTTP again through 8.8.8.8/1.1.1.1.

## Updating the firmware remotely

When a change under this folder is pushed to the `shtef` branch, the `wifi_diag_d1mini` workflow builds it. It publishes the result to the rolling `diag-fw` pre-release with `FW_VERSION` = run number. Send the `update` command above, then check `fw=` in `logs/<id>.seen`. TLS certificates are not verified (`setInsecure`).

## Reading the log

WiFi status: 0 idle, 1 SSID not found, 3 connected, 4 connect failed, 6 wrong password, 7 disconnected/connecting.
- "associated" with no status 3 means association worked but DHCP failed.

Disconnect reasons:
- 2 auth expired
- 8 left (normal, our own disconnect)
- 15 / 204 4-way handshake timeout (usually a wrong password, or WPA3/PMF only)
- 200 beacon timeout
- 201 AP not found
- 202 auth failed
- 203 association failed
