# WiFi Relay Control

Using ESP8266 modules with 4 relays to controll gates. The relay_server is a Flask based website to enable control over internet. The command is sent via MQTT server, but since my hosting blocks outbound connections to default mqtt port ,
I am using port above 42000.

The relay_server web service shows buttons you can use to trigger relays for about 1s, so they can be used to bypass existing pushbuttons and triger commands for controlling electric gates.


## How to start
- relay_server folder contains the server that you can deploy on a CGI based hosting or on your own server.
- relay_device_fw is an Arduino project for an ESP8266 based relay board
- licence_plate_recognize is a project I started as a proof of concept to see if a low end device like Raspberry Pi 4 can be used to recognize car plates and open the door automatically. It can, but I never finished integrating this into the server.
- 3D_Box is a FreeCad design to house the relay board and protect it from rain.

Each of these has a README.md in it's folder, so read the individual ones to start.