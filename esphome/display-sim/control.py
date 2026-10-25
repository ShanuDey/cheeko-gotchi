"""Control page for the display simulator.

    uv run --group sim esphome/display-sim/control.py

Starts the simulator (in WSL on Windows) and a page at http://localhost:8081 where you change the
expression, voice state, color, frame rate and shape fields while it runs. The page writes
settings.txt, which the simulator polls. See README.md.
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
    app = create_app(meta, SettingsFile(meta))

    simulator = Simulator(args.distro)
    if not args.no_sim:
        simulator.start()
    url = f"http://localhost:{args.port}"
    if not args.no_browser:
        threading.Timer(1.5, webbrowser.open, args=[url]).start()
    print(f"control page: {url}")
    try:
        uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
    finally:
        simulator.stop()


if __name__ == "__main__":
    main()
