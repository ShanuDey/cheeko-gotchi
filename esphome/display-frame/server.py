"""Serve a snapshot of a web page as a 240x296 JPEG at /frame.jpg.

The page is one of the bundled pages/*.html (/frame.jpg?page=<name>, listed at /presets),
or a custom /frame.jpg?url=<page>; with neither, the first bundled page is shown.
?margin=<px> sets the black border for that request (default MARGIN_PX). Custom URLs must
be http(s), and ALLOWED_HOSTS can restrict http(s) further, so the service is not an open
proxy.
"""
import io
import os
import re
import socket
import socketserver
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

from PIL import Image
from playwright.sync_api import sync_playwright

PAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages")
PAGE_NAME = re.compile(r"[a-z0-9_-]+")
PORT = 28240  # keep in sync with ports: in docker-compose.yaml and EXPOSE in the Dockerfile
WIDTH, HEIGHT = 240, 296
NAV_TIMEOUT_MS = 20000
SETTLE_MS = 500
CLIENT_TIMEOUT_S = 10
MAX_FAILURES = 5
MAX_MARGIN_PX = 20

MARGIN_PX = int(os.environ.get("MARGIN_PX", "0"))  # default; a request can override with ?margin=
JPEG_QUALITY = int(os.environ.get("JPEG_QUALITY", "80"))
REFRESH_SECONDS = float(os.environ.get("REFRESH_SECONDS", "30"))
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Kolkata")
# Opt-in: publish Chromium's DevTools (chrome://inspect) on the container's port 9222.
# Anyone who can reach it controls the browser, so leave it off unless debugging.
# Chromium only listens on localhost (it ignores --remote-debugging-address), so it uses
# CHROMIUM_DEBUG_PORT and a relay re-publishes it on DEBUG_PORT.
DEVTOOLS = os.environ.get("DEVTOOLS", "") not in ("", "0")
DEBUG_PORT = 9222  # keep in sync with the DevTools mapping in docker-compose.yaml
CHROMIUM_DEBUG_PORT = 9221
USER_DATA_DIR = os.environ.get("USER_DATA_DIR", "")  # keeps logins and cookies between restarts
ALLOWED_HOSTS = {h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()}

if not 0 <= MARGIN_PX <= MAX_MARGIN_PX:
    raise SystemExit(f"MARGIN_PX must be 0 to {MAX_MARGIN_PX}, got {MARGIN_PX}")
if not 1 <= JPEG_QUALITY <= 95:
    raise SystemExit(f"JPEG_QUALITY must be 1 to 95, got {JPEG_QUALITY}")


def viewport(margin):
    """The page renders inside the margin and is pasted onto a black canvas."""
    return {"width": WIDTH - 2 * margin, "height": HEIGHT - 2 * margin}


def preset_names():
    """Bundled pages the device can pick from, e.g. ["clock"]."""
    names = (f[:-5] for f in os.listdir(PAGES_DIR) if f.endswith(".html"))
    return sorted(n for n in names if PAGE_NAME.fullmatch(n))


def allowed(url):
    """Custom pages the device may request: http(s) only.

    file:// is refused (bundled pages go through ?page=): a percent-encoded ".." slips past
    any string check on the path and Chromium would decode it. ALLOWED_HOSTS (comma
    separated) narrows http(s) to those hosts when set, so the service is not an open
    proxy to everything on the network.
    """
    parts = urlsplit(url)
    if parts.scheme in ("http", "https") and parts.hostname:
        return not ALLOWED_HOSTS or parts.hostname in ALLOWED_HOSTS
    return False


class Browser:
    def __init__(self, playwright):
        self.playwright = playwright
        self.chromium = None
        self.start()

    def start(self):
        if self.chromium is not None:
            try:
                self.chromium.close()
            except Exception:
                pass
        # The container lacks the privileges Chromium's sandbox needs.
        args = ["--no-sandbox"]
        if DEVTOOLS:
            args.append(f"--remote-debugging-port={CHROMIUM_DEBUG_PORT}")
        view = {"viewport": viewport(MARGIN_PX), "timezone_id": TIMEZONE}
        if USER_DATA_DIR:
            # A recreated container has a new hostname, which Chromium reads as another
            # machine holding the profile, so drop the stale lock files first.
            for lock in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
                try:
                    os.remove(os.path.join(USER_DATA_DIR, lock))
                except OSError:
                    pass
            self.chromium = self.playwright.chromium.launch_persistent_context(
                USER_DATA_DIR, args=args, **view
            )
            self.page = self.chromium.pages[0] if self.chromium.pages else self.chromium.new_page()
        else:
            self.chromium = self.playwright.chromium.launch(args=args)
            self.page = self.chromium.new_page(**view)
        self.margin = MARGIN_PX
        self.url = None
        self.loaded_at = 0.0
        self.failures = 0

    def frame(self, url, margin):
        if margin != self.margin:
            # Pages lay out for the viewport, so a new margin needs a resize and a reload.
            self.page.set_viewport_size(viewport(margin))
            self.margin = margin
            self.url = None
        if url != self.url or time.monotonic() - self.loaded_at > REFRESH_SECONDS:
            # "load", not "networkidle": pages that poll or hold a websocket never
            # go idle and would time out on every reload.
            self.page.goto(url, wait_until="load", timeout=NAV_TIMEOUT_MS)
            self.page.wait_for_timeout(SETTLE_MS)
            self.url = url
            self.loaded_at = time.monotonic()
        shot = Image.open(io.BytesIO(self.page.screenshot(type="png"))).convert("RGB")
        canvas = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        canvas.paste(shot, (margin, margin))
        out = io.BytesIO()
        canvas.save(out, format="JPEG", quality=JPEG_QUALITY)
        self.failures = 0
        return out.getvalue()

    def recover(self, exc):
        """Restart Chromium only if it died or keeps failing.

        A down site fails every request and the device retries about once a
        second, so restarting on every failure would burn CPU and memory.
        """
        self.failures += 1
        self.url = None
        self.loaded_at = 0.0
        message = str(exc).lower()
        # Not a bare "closed": net::ERR_CONNECTION_CLOSED is an ordinary site failure.
        dead = any(text in message for text in ("has been closed", "target closed", "crashed"))
        if dead or self.failures >= MAX_FAILURES:
            print("restarting browser", flush=True)
            self.start()


class DevToolsRelay(socketserver.ThreadingTCPServer):
    """Forward DEBUG_PORT on all interfaces to Chromium's localhost-only debug port."""

    allow_reuse_address = True
    daemon_threads = True


class RelayHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            upstream = socket.create_connection(("127.0.0.1", CHROMIUM_DEBUG_PORT), timeout=5)
        except OSError:
            return  # Chromium is restarting; the client retries

        def pipe(src, dst):
            try:
                while data := src.recv(65536):
                    dst.sendall(data)
            except OSError:
                pass
            finally:
                for sock in (src, dst):
                    try:
                        sock.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass

        upstream.settimeout(None)
        threading.Thread(target=pipe, args=(upstream, self.request), daemon=True).start()
        pipe(self.request, upstream)


def make_handler(browser):
    class Handler(BaseHTTPRequestHandler):
        timeout = CLIENT_TIMEOUT_S

        def do_GET(self):
            parts = urlsplit(self.path)
            if parts.path == "/health":
                self.reply(200, b"ok", "text/plain")
            elif parts.path == "/presets":
                self.reply(200, "\n".join(preset_names()).encode(), "text/plain")
            elif parts.path == "/frame.jpg":
                query = parse_qs(parts.query)
                try:
                    margin = int(query.get("margin", [MARGIN_PX])[0])
                except ValueError:
                    margin = -1
                if not 0 <= margin <= MAX_MARGIN_PX:
                    self.send_error(400, f"margin must be 0 to {MAX_MARGIN_PX}")
                    return
                if "url" in query and "page" not in query:
                    url = query["url"][0]
                    if not allowed(url):
                        self.send_error(400, "url not allowed")
                        return
                else:
                    names = preset_names()
                    name = query["page"][0] if "page" in query else (names[0] if names else "")
                    if name not in names:
                        self.send_error(400, "unknown page")
                        return
                    url = f"file://{PAGES_DIR}/{name}.html"
                self.send_frame(url, margin)
            else:
                self.send_error(404)

        def send_frame(self, url, margin):
            try:
                body = browser.frame(url, margin)
            except Exception as exc:
                print(f"frame failed: {exc}", flush=True)
                try:
                    browser.recover(exc)
                except Exception as restart_exc:
                    print(f"browser restart failed: {restart_exc}", flush=True)
                self.send_error(502, "frame unavailable")
                return
            self.reply(200, body, "image/jpeg")

        def reply(self, status, body, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            # No Last-Modified and no caching: the device would get 304s and stall.
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, fmt, *args):
            pass

    return Handler


if __name__ == "__main__":
    if DEVTOOLS:
        relay = DevToolsRelay(("0.0.0.0", DEBUG_PORT), RelayHandler)
        threading.Thread(target=relay.serve_forever, daemon=True).start()
        print(f"DevTools relay on port {DEBUG_PORT}", flush=True)
    with sync_playwright() as p:
        # Playwright's sync API is bound to this thread, so requests run one at a time.
        HTTPServer(("0.0.0.0", PORT), make_handler(Browser(p))).serve_forever()
