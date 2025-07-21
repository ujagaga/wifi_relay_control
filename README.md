# DualQuadRelayWiFiControl

Using ESP8266 modules with 4 relays to controll gates. The relay_server is a Flask based website to enable control over internet. The command is sent via MQTT server, but since my hosting blocks outbound connections to default mqtt port ,
I am using port above 42000.

Modules feature an Over The Air update mecanism. It does not have any security by default, but you can enable it by uncommenting the define in config: "#define ENABLE_UPDATE_PASSWORD".

To trigger the Over The Air update, just go to http page "/update". When asked for a password if you did not enable it, just type anything.

## NOTE

Device UI is available only in Acces Point mode, so at startup you nedd to connect to it and then you can configure it.

## How to start

1. Install Arduino IDE.
2. In "File/Preferences" add to "Additional Boards Manager":

        https://arduino.esp8266.com/stable/package_esp8266com_index.json


2. Install additional libraries: "ArduinoJson", "WebSockets" and "ESP_EEPROM"
3. In "config.h" adjust as needed:

- Change default 

        #define PASSWORD "abc131313" 
        
  to something only you will know
- Choose whether to use password for OTA update using 

        #define ENABLE_UPDATE_PASSWORD
        
  The network should be closed and no unauthorized people should not have access, so it should be safe enough without password.
- Change the 

        #define AP_NAME_PREFIX "Zaric_sw_"

4. Connect your module for initial programming
5. Select ESP-12 board and
6. build and program using a USB UART module. For any further firmware updates, you can use the Over The Air update. To use it:
- Connect to device's WiFi network or your home LAN if you have already configured your device to connect to it.
- Using your web browser, go to "/update" page to trigger the update.
- It takes a while, up to 30 seconds for Arduino IDE to detect the new update server and list it in "Tools/Port" for you to select. 
- Click on the program button in Arduino IDE. The Arduino IDE will ask for password. If you have not set any, just use what ever.

## Note

The module I used can be powered from either one of:
1. 5V DC
2. 7V to 30V DC
3. 220V AC

The relays all have 3 pins: Normally Open, Normally Closed and Common.
By default relays are triggered by pins 12, 13, 14 and 16, but pin 16 is active on boot and triggeres a relay for about a second. I used pin 5 instead to avoid this.

## Status
Finished