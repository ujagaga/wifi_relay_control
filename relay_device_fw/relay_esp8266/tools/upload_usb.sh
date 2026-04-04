#!/usr/bin/env bash

PROJECT_NAME="relay_esp8266"
PYTHON="$HOME/.arduino15/packages/esp8266/tools/python3/3.7.2-post1/python3"
ESP_TOOL="$HOME/.arduino15/packages/esp8266/hardware/esp8266/3.1.2/tools/esptool/esptool.py"

# Get the path of the script as it was called (might be a symlink)
SCRIPT_PATH="$BASH_SOURCE"
# Resolve the symlink, if it is one, to get the actual file path
while [ -h "$SCRIPT_PATH" ]; do
  SCRIPT_PATH=$(readlink "$SCRIPT_PATH")
done
# Get the directory of the resolved script path
SCRIPT_DIR=$(dirname "${SCRIPT_PATH}")

cd "${SCRIPT_DIR}"
echo "Uploading from ../build"

${PYTHON} ${ESP_TOOL} --chip esp8266 --port /dev/ttyUSB0 --baud 460800 \
--before default-reset --after hard-reset write-flash \
--flash-mode dio --flash-freq 80m --flash-size detect \
0x0 ../build/${PROJECT_NAME}.ino.bin
