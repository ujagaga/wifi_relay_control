# WiFi Relay

Using ESP8266/ESP32 modules with up to 4 (easy to expand to more) relays to controll gates. The relay_server is a Flask based website to enable control over internet. This device pings the server at 2s intervals to check for any new command.

The commands are json based data:
1. Trigger a relay: {"relay_id": <id:0..3>,"command": "unlock"}
2. Restart device: {"command": "restart"}
3. Update firmware: {"command": "update", "firmware": "<firmware_id>"}

## NOTE

Device UI is available only in Acces Point mode, so at startup you nedd to connect to it and then you can configure the WiFi connection.

## How to start

1. Install Arduino IDE.
2. In "File/Preferences" add to "Additional Boards Manager":
	a: For ESP8266: `https://arduino.esp8266.com/stable/package_esp8266com_index.json`
	b: For ESP32: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`

3. Install additional libraries: "ArduinoJson", "WebSockets" and "ESP_EEPROM"
4. In "config.h" adjust as needed:

- Change default 

        #define PASSWORD "abc121212" 
        
  to something only you will know

- Change the 

        #define REPORT_URL "reverse_http_tunnel_http.url" 

  to your deployed server http url

4. Connect your module for initial programming
5. Select correct board 
6. build and program using a USB UART module. For any further firmware updates, you can use the server as it features a firmware upload and activation. To locate the firmware,
go to `Arduino IDE => Sketch => Export Compiled Binary`. Your binary will be located in the sketch folder.

## Note

The module I used can be powered from either one of:
1. 5V DC
2. 7V to 30V DC
3. 220V AC

The relays all have 3 pins: Normally Open, Normally Closed and Common.
By default, on ESP8266 relays are triggered by pins 12, 13, 14 and 16, but pin 16 is active on boot and triggeres a relay for about a second. I used pin 5 instead to avoid this.
