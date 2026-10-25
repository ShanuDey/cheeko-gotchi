"""Control page for the display simulator: a small FastAPI app that edits settings.txt.

    meta      what can be set, read from the face component's headers (no second copy)
    settings  the settings model and the settings.txt reader and writer
    api       the FastAPI routes
    launcher  starts, stops and restarts the simulator itself (in WSL on Windows)
"""
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parents[1]            # esphome/display-sim
FACE_DIR = SIM_DIR.parent / "components" / "face"        # esphome/components/face
SETTINGS_PATH = SIM_DIR / "settings.txt"
SETTINGS_EXAMPLE_PATH = SIM_DIR / "settings.example.txt"
WEB_DIR = SIM_DIR / "web"
