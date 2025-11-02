# WiFi Relay Control

Using ESP8266/ESP32 modules with 4 relays to controll gates. The relay_server is a Flask based website to enable control over internet. 
The relay_server web service shows buttons you can use to trigger relays for about 1s, so they can be used to bypass existing pushbuttons and triger commands for controlling electric gates.


## How to start
- relay_server folder contains the Python Flask server to controll the relays.
- relay_device_fw is a collection of Arduino projects for ESP8266 and ESP32 based relay boards. 
- licence_plate_recognize is a project I started as a proof of concept to see if a low end device like Raspberry Pi 4 can be used to recognize car plates and open the door automatically. It can, but I never finished integrating this into the server and do not intend to unless there is an interest in it.
- 3D_Box is a FreeCad design to house the relay board and protect it from rain.

Each of these has a README.md in it's folder, so read the individual ones to start.