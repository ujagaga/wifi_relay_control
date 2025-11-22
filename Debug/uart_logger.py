#!/usr/bin/env python3
import serial
import time
import os
from datetime import datetime

# ---- CONFIG ----
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200
LOG_DIR = "logs"


# -----------------

def get_log_filename(now):
    return now.strftime("%Y-%m-%d_%H.log")


def write_plain(logfile, ts, msg):
    line = f"{ts}  {msg}"
    logfile.write(line + "\n")
    print(line)


def write_compressed(logfile, ts_start, ts_end, msg, count):
    line = f"{ts_start} - {ts_end} ({count} repeats): {msg}"
    logfile.write(line + "\n")
    print(line)


def flush_block(logfile, msg, ts_start, ts_end, count):
    """Flush either a single message or a compressed range."""
    if msg is None:
        return

    if count == 1:
        write_plain(logfile, ts_start, msg)
    else:
        write_compressed(logfile, ts_start, ts_end, msg, count)


def main():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    print(f"Opening serial port {SERIAL_PORT} @ {BAUD_RATE} baud...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

    # Setup first log file
    now = datetime.now()
    current_filename = get_log_filename(now)
    logfile_path = os.path.join(LOG_DIR, current_filename)
    logfile = open(logfile_path, "a", buffering=1)
    print(f"Logging to {logfile_path}")

    # Variables for repeated message detection
    last_msg = None
    ts_start = None
    ts_end = None
    repeat_count = 0

    try:
        while True:
            raw = ser.readline()

            if raw:
                try:
                    msg = raw.decode(errors="replace").rstrip()
                except:
                    msg = repr(raw)

                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if last_msg is None:
                    # First message ever
                    last_msg = msg
                    ts_start = ts
                    ts_end = ts
                    repeat_count = 1

                elif msg == last_msg:
                    # Extend repeated block
                    repeat_count += 1
                    ts_end = ts

                else:
                    # Different message → flush previous block
                    flush_block(logfile, last_msg, ts_start, ts_end, repeat_count)

                    # Start new block
                    last_msg = msg
                    ts_start = ts
                    ts_end = ts
                    repeat_count = 1

                # Hourly rotation check
                now = datetime.now()
                new_filename = get_log_filename(now)

                if new_filename != current_filename:
                    # Flush current block before switching files
                    flush_block(logfile, last_msg, ts_start, ts_end, repeat_count)
                    last_msg = None

                    logfile.close()
                    print(f"--- Switched to new log file {new_filename} ---")
                    current_filename = new_filename
                    logfile_path = os.path.join(LOG_DIR, new_filename)
                    logfile = open(logfile_path, "a", buffering=1)

            time.sleep(0.005)

    except KeyboardInterrupt:
        print("Stopping logger...")

    finally:
        # Final flush
        flush_block(logfile, last_msg, ts_start, ts_end, repeat_count)

        logfile.close()
        ser.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
