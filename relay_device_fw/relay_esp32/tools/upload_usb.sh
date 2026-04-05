#!/usr/bin/env bash

PROJECT_NAME="relay_esp32"
PYTHON="/usr/bin/python3"
ESP_TOOL="$HOME/.arduino15/packages/esp32/tools/esptool_py/4.5.1/esptool.py"

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

${PYTHON} ${ESP_TOOL} --chip esp32 --port /dev/ttyUSB0 --baud 460800 \
--before default_reset --after hard_reset write_flash \
--flash_mode dio --flash_freq 80m --flash_size detect \
0x1000 ../build/${PROJECT_NAME}.ino.bootloader.bin \
0x8000 ../build/${PROJECT_NAME}.ino.partitions.bin \
0x10000 ../build/${PROJECT_NAME}.ino.bin
