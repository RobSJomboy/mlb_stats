#!/usr/bin/env python3
"""
Trade Snapshot — relay for an OBS Browser Source, on this machine or another one.

Why you'd run this: an OBS Browser Source is its own little browser, so it can't
hear the control page's BroadcastChannel or read its localStorage. This holds the
current on-air lower third in memory, the control page POSTs to it, and the
display view polls it — over the network if the two are on different computers.

    python3 trade_snapshot_server.py

Run it on the laptop you're driving from. It binds every interface, so the OBS
machine on the same network can reach it; the banner prints the exact URL to paste
into the Browser Source. Pass --local to keep it on 127.0.0.1 instead.

If you only ever need a second window on the same computer, you don't need this at
all — the control page and a plain ?display=1 tab talk to each other directly.

Stop it with Ctrl+C. Nothing is written to disk; state resets on restart.
"""

import json
import os
import secrets
import socket
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORT = int(os.environ.get("PORT", 8787))
ROOT = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(ROOT, ".relay_key")

# The lower third that's currently on air. Replaced wholesale on every POST from
# the control page; {"clear": True} takes the bar off screen.
STATE = {"clear": True, "ts": 0}

LOOPBACK = ("127.0.0.1", "::1")


def load_key(rotate=False):
    """The shared key, kept in .relay_key so it survives restarts.

    Stable on purpose: a key that changed every launch would mean re-pasting the
    Browser Source URL in OBS before every show, which is exactly the friction
    this is supposed to avoid. --new-key rotates it if it ever leaks.
    """
    if not rotate and os.path.exists(KEY_FILE):
        try:
            existing = open(KEY_FILE).read().strip()
            if existing:
                return existing
        except OSError:
            pass
    key = secrets.token_urlsafe(8)
    with open(KEY_FILE, "w") as f:
        f.write(key)
    try:
        os.chmod(KEY_FILE, 0o600)
    except OSError:
        pass
    return key


KEY = load_key("--new-key" in sys.argv)


def lan_ip():
    """This machine's address on the local network, as the OBS box would dial it.

    Opening a UDP socket toward a public address sends no packets — it just makes
    the OS pick the interface it would route out of, which is the one the other
    computer in the room can see. Beats hostname lookups, which on macOS love to
    come back 127.0.0.1.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


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

    # ── access ──
    def _is_local(self):
        return self.client_address[0] in LOOPBACK

    def _authorized(self):
        """Loopback is trusted; everyone else needs the key.

        That split is the whole point: the control page runs on this machine, so
        it never has to know the key, and the only URL anyone has to carry around
        is the one for the OBS box — which the banner hands them fully built.
        """
        if self._is_local():
            return True
        given = (parse_qs(urlparse(self.path).query).get("key") or [None])[0] \
            or self.headers.get("X-Relay-Key")
        return bool(given) and secrets.compare_digest(given, KEY)

    # ── routes ──
    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        if not self._authorized():
            return self._json({"error": "bad or missing key"}, 403)
        path = self.path.split("?")[0]
        if path == "/state":
            return self._json(STATE)
        if path == "/info":
            # lets the control page show the OBS-machine URL without anyone
            # having to go hunting through Network settings for an IP. The key
            # only goes to loopback — handing it to the network would defeat it.
            info = {"host": lan_ip(), "port": PORT}
            if self._is_local():
                info["key"] = KEY
            return self._json(info)
        if path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def list_directory(self, path):
        # no directory listings — this is reachable from the rest of the network
        self.send_error(404, "Not Found")
        return None

    def do_POST(self):
        global STATE
        if not self._authorized():
            return self._json({"error": "bad or missing key"}, 403)
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
    local_only = "--local" in sys.argv
    bind = "127.0.0.1" if local_only else "0.0.0.0"
    host = "localhost" if local_only else lan_ip()

    srv = ThreadingHTTPServer((bind, PORT), Handler)
    print("\n  TRADE SNAPSHOT — OBS relay")
    print("  " + "-" * 64)
    print("  On this laptop, open:")
    print("      http://localhost:%d/index.html" % PORT)
    print()
    if local_only:
        print("  OBS Browser Source (this computer only — started with --local):")
        print("      http://localhost:%d/index.html?display=1&src=server" % PORT)
    else:
        print("  OBS Browser Source, 1920x1080 — paste this on the OBS computer:")
        print("      http://%s:%d/index.html?display=1&src=server&key=%s" % (host, PORT, KEY))
        print()
        print("  The key is already in that URL — nothing to type. It stays the same")
        print("  across restarts, so OBS keeps working once it's set up.")
        print("  (--new-key rotates it, --local turns the network off entirely.)")
        print()
        print("  Both machines have to be on the same network. If OBS can't reach it,")
        print("  it's almost always the firewall on this laptop blocking Python.")
    print("  " + "-" * 64)
    print("  serving %s" % ROOT)
    print("  Ctrl+C to stop\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  stopped\n")
        srv.shutdown()


if __name__ == "__main__":
    main()
