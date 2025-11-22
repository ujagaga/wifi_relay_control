## Debug

My ESP8266 device gets disconnected and will not show up again. 
After a power cycle it works. I need to figure out why this hapends, so I created this logger to analyze the UART debug messages.
It connects to a /dev/ttyUSB0 port (assigned at the script beginning, so feel free to adjust) and logs all UART messages in text files rotated each hour.
Since the device operation results in many rows with same message, any 10 rows with same message are compressed into one message.
