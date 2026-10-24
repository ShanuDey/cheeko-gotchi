"""Serve a screenshot of one fixed page as a 240x296 JPEG at /frame.jpg.

The page comes from TARGET_URL, never from the request, so the service cannot be
used as a proxy to other hosts on the network.
"""
import io
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from PIL import Image
from playwright.sync_api import sync_playwright

PORT = 28240  # keep in sync with ports: in docker-compose.yaml and EXPOSE in the Dockerfile
WIDTH, HEIGHT = 240, 296
NAV_TIMEOUT_MS = 20000
SETTLE_MS = 500
CLIENT_TIMEOUT_S = 10
MAX_FAILURES = 5

TARGET_URL = os.environ["TARGET_URL"]
MARGIN_PX = int(os.environ.get("MARGIN_PX", "20"))
JPEG_QUALITY = int(os.environ.get("JPEG_QUALITY", "80"))
REFRESH_SECONDS = float(os.environ.get("REFRESH_SECONDS", "30"))
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Kolkata")

if not 0 <= MARGIN_PX < min(WIDTH, HEIGHT) // 2:
    raise SystemExit(f"MARGIN_PX must be 0 to {min(WIDTH, HEIGHT) // 2 - 1}, got {MARGIN_PX}")
if not 1 <= JPEG_QUALITY <= 95:
    raise SystemExit(f"JPEG_QUALITY must be 1 to 95, got {JPEG_QUALITY}")


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
        self.chromium = self.playwright.chromium.launch(args=["--no-sandbox"])
        # The page renders inside the margin and is pasted onto a black canvas.
        self.page = self.chromium.new_page(
            viewport={"width": WIDTH - 2 * MARGIN_PX, "height": HEIGHT - 2 * MARGIN_PX},
            timezone_id=TIMEZONE,
        )
        self.loaded_at = 0.0
        self.failures = 0

    def frame(self):
        if time.monotonic() - self.loaded_at > REFRESH_SECONDS:
            # "load", not "networkidle": pages that poll or hold a websocket never
            # go idle and would time out on every reload.
            self.page.goto(TARGET_URL, wait_until="load", timeout=NAV_TIMEOUT_MS)
            self.page.wait_for_timeout(SETTLE_MS)
            self.loaded_at = time.monotonic()
        shot = Image.open(io.BytesIO(self.page.screenshot(type="png"))).convert("RGB")
        canvas = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        canvas.paste(shot, (MARGIN_PX, MARGIN_PX))
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
        self.loaded_at = 0.0
        message = str(exc).lower()
        # Not a bare "closed": net::ERR_CONNECTION_CLOSED is an ordinary site failure.
        dead = any(text in message for text in ("has been closed", "target closed", "crashed"))
        if dead or self.failures >= MAX_FAILURES:
            print("restarting browser", flush=True)
            self.start()


def make_handler(browser):
    class Handler(BaseHTTPRequestHandler):
        timeout = CLIENT_TIMEOUT_S

        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/health":
                self.reply(200, b"ok", "text/plain")
            elif path == "/frame.jpg":
                self.send_frame()
            else:
                self.send_error(404)

        def send_frame(self):
            try:
                body = browser.frame()
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
    with sync_playwright() as p:
        # Playwright's sync API is bound to this thread, so requests run one at a time.
        HTTPServer(("0.0.0.0", PORT), make_handler(Browser(p))).serve_forever()
