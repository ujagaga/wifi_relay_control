#!/usr/bin/env python3
"""
Temporary server for the wifi_diag_d1mini firmware. Python standard library only.

    python3 diag_server.py [port]       (default 8090)

Queue a command for a device by writing  cmd/<device_id>.json  (delivered once, then renamed to .sent).
Logs uploaded by a device are appended to  logs/<device_id>.log,  last poll info is in  logs/<device_id>.seen
"""
import os
import re
import sys
import time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CMD_DIR = os.path.join(BASE_DIR, "cmd")
LOG_DIR = os.path.join(BASE_DIR, "logs")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8090


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


class Handler(BaseHTTPRequestHandler):
    def reply(self, body, code=200, ctype="text/plain"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def client_ip(self):
        return self.headers.get("X-Real-IP", self.client_address[0])  # Set by the nginx proxy.

    def device_id(self, query):
        dev_id = query.get("id", [""])[0]
        return dev_id if re.fullmatch(r"[A-Za-z0-9_]{1,40}", dev_id) else None

    def do_GET(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)

        if url.path == "/diag/ping":
            return self.reply("pong")

        if url.path == "/diag/blob":
            size = min(int(query.get("size", ["1000"])[0]), 65536)
            return self.reply(b"x" * size)

        if url.path == "/diag/poll":
            dev_id = self.device_id(query)
            if not dev_id:
                return self.reply("bad id", 400)
            info = " ".join(f"{k}={v[0]}" for k, v in query.items() if k != "id")
            with open(os.path.join(LOG_DIR, dev_id + ".seen"), "w") as f:
                f.write(f"{now()} from {self.client_ip()} {info}\n")

            cmd_file = os.path.join(CMD_DIR, dev_id + ".json")
            if os.path.exists(cmd_file):
                with open(cmd_file) as f:
                    cmd = f.read()
                os.replace(cmd_file, cmd_file + ".sent")
                print(f"{now()} sent to {dev_id}: {cmd.strip()}", flush=True)
                return self.reply(cmd, ctype="application/json")
            return self.reply("{}", ctype="application/json")

        self.reply("not found", 404)

    def do_POST(self):
        url = urlparse(self.path)
        dev_id = self.device_id(parse_qs(url.query))
        if url.path != "/diag/log" or not dev_id:
            return self.reply("not found", 404)

        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        with open(os.path.join(LOG_DIR, dev_id + ".log"), "ab") as f:
            f.write(f"----- received {now()} from {self.client_ip()}\n".encode())
            f.write(body)
        print(f"{now()} log from {dev_id}: {len(body)} bytes", flush=True)
        self.reply("OK")

    def log_message(self, fmt, *args):
        pass  # Devices poll every few seconds, keep stdout for commands and logs only.


if __name__ == "__main__":
    os.makedirs(CMD_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    print(f"{now()} diag server on port {PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
