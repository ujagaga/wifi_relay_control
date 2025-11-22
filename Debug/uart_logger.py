#!/usr/bin/env python3

import serial
import time
import os
from datetime import datetime

# --- CONFIGURATION ---
SERIAL_PORT = "/dev/ttyUSB0"   # Change to your port
BAUD_RATE = 115200             # Change if needed
LOG_DIR = "logs"               # Folder where logs will be stored
# ----------------------

def get_log_filename(now):
    """Return filename based on current date and hour."""
    return now.strftime("%Y-%m-%d_%H.log")

def main():
    # Ensure log directory exists
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    print(f"Opening serial port {SERIAL_PORT} @ {BAUD_RATE} baud...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

    # Start with current hour file
    now = datetime.now()
    current_filename = get_log_filename(now)
    current_path = os.path.join(LOG_DIR, current_filename)

    logfile = open(current_path, "a", buffering=1)
    print(f"Logging to {current_path}")

    try:
        while True:
            line = ser.readline()

            if line:
                try:
                    decoded = line.decode(errors="replace").rstrip()
                except:
                    decoded = repr(line)

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logfile.write(f"{timestamp}  {decoded}\n")

                # Also live-print to console
                print(f"{timestamp}  {decoded}")

            # Check if hour has changed
            now = datetime.now()
            new_filename = get_log_filename(now)

            if new_filename != current_filename:
                # Close previous file
                logfile.close()
                print(f"--- Switched to new log file {new_filename} ---")

                # Open new file
                current_filename = new_filename
                current_path = os.path.join(LOG_DIR, current_filename)
                logfile = open(current_path, "a", buffering=1)

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("Stopping logger...")
    finally:
        logfile.close()
        ser.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
