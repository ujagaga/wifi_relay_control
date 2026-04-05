#!/usr/bin/env bash

# Install arduino-cli (if not already installed):
#
#   Linux/macOS:
#     curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
#     sudo mv bin/arduino-cli /usr/local/bin/
#
#   Or via snap (Linux):
#     sudo snap install arduino-cli
#
#   After installing, initialize the config:
#     arduino-cli config init
#
#   For ESP32 support, add the board manager URL to the config:
#     arduino-cli config add board_manager.additional_urls https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

# Install ESP32 platform
arduino-cli core update-index
arduino-cli core install esp32:esp32

# Install required libraries
arduino-cli lib install "ArduinoJson"
arduino-cli lib install "PubSubClient"
arduino-cli lib install "WebSockets"
