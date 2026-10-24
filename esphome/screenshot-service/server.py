"""Serve a headless-browser screenshot of one fixed page as a 240x296 JPEG.

The Cheeko Gotchi fetches /frame.jpg in a loop (see ../README.md, Video). The
page is fixed by TARGET_URL on purpose: taking the URL from the request would
make this an open proxy to anything on your network.
"""
import io
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from PIL import Image
from playwright.sync_api import sync_playwright

TARGET_URL = os.environ["TARGET_URL"]
WIDTH, HEIGHT = 240, 296
MARGIN_PX = int(os.environ.get("MARGIN_PX", "20"))        # keeps content out of the rounded corners
JPEG_QUALITY = int(os.environ.get("JPEG_QUALITY", "80"))
REFRESH_SECONDS = float(os.environ.get("REFRESH_SECONDS", "30"))  # full page reload interval
PORT = int(os.environ.get("PORT", "8080"))
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Kolkata")   # IANA name; the container itself runs in UTC
CLIENT_TIMEOUT = 10   # seconds; a stalled client must not block the single-threaded server


class Browser:
    def __init__(self, playwright):
        self.playwright = playwright
        self.chromium = None
        self.start()

    def start(self):
        """Launch a fresh browser and page; also the recovery path after a crash."""
        if self.chromium is not None:
            try:
                self.chromium.close()
            except Exception:
                pass
        # --no-sandbox: Chromium's sandbox needs privileges the container does not have.
        self.chromium = self.playwright.chromium.launch(args=["--no-sandbox"])
        # The page renders at the inner size and is pasted onto a black canvas, so
        # the margin sits where the bezel hides the corners.
        self.page = self.chromium.new_page(
            viewport={"width": WIDTH - 2 * MARGIN_PX, "height": HEIGHT - 2 * MARGIN_PX},
            timezone_id=TIMEZONE,
        )
        self.loaded_at = 0.0

    def frame(self):
        if time.monotonic() - self.loaded_at > REFRESH_SECONDS:
            self.page.goto(TARGET_URL, wait_until="networkidle", timeout=20000)
            self.loaded_at = time.monotonic()
        shot = Image.open(io.BytesIO(self.page.screenshot(type="png"))).convert("RGB")
        canvas = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        canvas.paste(shot, (MARGIN_PX, MARGIN_PX))
        out = io.BytesIO()
        canvas.save(out, format="JPEG", quality=JPEG_QUALITY)
        return out.getvalue()


def make_handler(browser):
    class Handler(BaseHTTPRequestHandler):
        timeout = CLIENT_TIMEOUT

        def do_GET(self):
            if self.path.split("?")[0] == "/health":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")
                return
            if self.path.split("?")[0] != "/frame.jpg":
                self.send_error(404)
                return
            try:
                body = browser.frame()
            except Exception as exc:
                print(f"frame failed: {exc}", flush=True)
                try:
                    browser.start()   # the page or browser may have crashed: start over
                except Exception as restart_exc:
                    print(f"browser restart failed: {restart_exc}", flush=True)
                self.send_error(502, "frame unavailable")
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(body)))
            # No Last-Modified and no caching: the device would otherwise get 304s.
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            pass

    return Handler


if __name__ == "__main__":
    with sync_playwright() as p:
        # One request at a time: Playwright's sync API is bound to this thread.
        HTTPServer(("0.0.0.0", PORT), make_handler(Browser(p))).serve_forever()
