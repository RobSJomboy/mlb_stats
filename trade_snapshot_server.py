#!/usr/bin/env python3
"""
Trade Snapshot — optional local relay for an OBS Browser Source.

Why you'd run this: an OBS Browser Source is its own little browser, so it can't
hear the control page's BroadcastChannel or read its localStorage. This holds the
current on-air lower third in memory, the control page POSTs to it, and the
display view polls it.

    python3 trade_snapshot_server.py

Then in OBS add a Browser Source (1920x1080) pointed at:
    http://localhost:8787/index.html?display=1&src=server

...and run the control page at:
    http://localhost:8787/index.html

If you only ever need a second window on a second monitor, you don't need this at
all — the control page and a plain ?display=1 tab talk to each other directly.

Stop it with Ctrl+C. Nothing is written to disk; state resets on restart.
"""

import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", 8787))
ROOT = os.path.dirname(os.path.abspath(__file__))

# The lower third that's currently on air. Replaced wholesale on every POST from
# the control page; {"clear": True} takes the bar off screen.
STATE = {"clear": True, "ts": 0}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    # ── plumbing ──
    def end_headers(self):
        # Every response gets CORS: the control page may be opened straight from
        # file:// (origin "null") and still needs to POST state here.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        super().end_headers()

    def _json(self, payload, code=200):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.end_headers()
        self.wfile.write(body)

    # ── routes ──
    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/state":
            return self._json(STATE)
        if path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        global STATE
        if self.path.split("?")[0] != "/state":
            return self._json({"error": "not found"}, 404)
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            STATE = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            return self._json({"error": "bad json: %s" % e}, 400)
        return self._json({"ok": True})

    def log_message(self, fmt, *args):
        # keep the console quiet — the display polls /state a few times a second
        line = " ".join(str(a) for a in args)
        if "/state" in line:
            return
        sys.stderr.write("  %s\n" % (fmt % args))


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("\n  TRADE SNAPSHOT — OBS relay")
    print("  " + "-" * 56)
    print("  control   http://localhost:%d/index.html" % PORT)
    print("  overlay   http://localhost:%d/index.html?display=1&src=server" % PORT)
    print("  serving   %s" % ROOT)
    print("  " + "-" * 56)
    print("  Ctrl+C to stop\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  stopped\n")
        srv.shutdown()


if __name__ == "__main__":
    main()
