"""Control page for the display simulator.

    uv run --group sim esphome/display-sim/control.py

Starts the simulator (in WSL on Windows) and a page at http://localhost:8081 where you change the
expression, voice state, color and frame rate while it runs, like Home Assistant does on the
device. The page writes settings.txt, which the simulator polls. See README.md.
"""
import argparse
import threading
import webbrowser

import uvicorn

from simctl.api import create_app
from simctl.launcher import Simulator
from simctl.meta import load_meta
from simctl.settings import SettingsFile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--no-sim", action="store_true", help="only serve the page; start the simulator yourself")
    parser.add_argument("--no-browser", action="store_true", help="do not open the page in a browser")
    parser.add_argument("--distro", default="Ubuntu", help="WSL distribution that runs the simulator (Windows only)")
    args = parser.parse_args()

    meta = load_meta()   # fails early, with a clear message, if looks.h is not in the expected style
    simulator = Simulator(args.distro, managed=not args.no_sim)
    app = create_app(meta, SettingsFile(meta), simulator)

    if simulator.managed:
        simulator.start()
    url = f"http://localhost:{args.port}"
    if not args.no_browser:
        threading.Timer(1.5, webbrowser.open, args=[url]).start()
    print(f"control page: {url}")
    try:
        # The page keeps a connection open and polls, so do not wait long for it on Ctrl+C.
        uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning", timeout_graceful_shutdown=2)
    finally:
        simulator.stop()


if __name__ == "__main__":
    main()
