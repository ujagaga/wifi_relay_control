#!/usr/bin/env bash

# Get the path of the script as it was called (might be a symlink)
SCRIPT_PATH="$BASH_SOURCE"
# Resolve the symlink, if it is one, to get the actual file path
while [ -h "$SCRIPT_PATH" ]; do
  SCRIPT_PATH=$(readlink "$SCRIPT_PATH")
done
# Get the directory of the resolved script path
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")

cd $SCRIPT_DIR
rm -rf ../build


echo "Building relay_esp8266"
/usr/local/bin/arduino-cli compile --fqbn esp8266:esp8266:nodemcuv2 \
--build-path ../build \
..
